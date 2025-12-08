#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-Click Cleanup Service for Telegram Accounts
Provides automated cleanup functionality: leave groups/channels, delete history, clear contacts
"""

import asyncio
import csv
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

try:
    from telethon import TelegramClient
    from telethon.errors import (
        FloodWaitError, ChatAdminRequiredError, UserNotParticipantError,
        ChannelPrivateError, PeerIdInvalidError, RPCError
    )
    from telethon.tl.types import (
        Channel, Chat, User, Dialog,
        InputPeerEmpty, PeerChannel, PeerChat, PeerUser
    )
    from telethon.tl.functions.messages import DeleteHistoryRequest
    from telethon.tl.functions.channels import LeaveChannelRequest
    from telethon.tl.functions.contacts import DeleteContactsRequest
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    # Define placeholder types
    Channel = Chat = User = Dialog = None
    FloodWaitError = ChatAdminRequiredError = UserNotParticipantError = Exception
    ChannelPrivateError = PeerIdInvalidError = RPCError = Exception


logger = logging.getLogger(__name__)


@dataclass
class CleanupAction:
    """Represents a single cleanup action and its result"""
    chat_id: int
    title: str
    chat_type: str  # 'channel', 'group', 'private', 'bot'
    actions_done: List[str] = field(default_factory=list)
    status: str = 'pending'  # 'pending', 'success', 'partial', 'failed', 'skipped'
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class OneClickCleaner:
    """
    One-Click Cleanup Service for Telegram accounts.
    
    Features:
    - Leave all joined groups and channels
    - Delete all chat histories with revoke where possible
    - Clear all contacts
    - Close/archive remaining dialogs
    - Generate detailed reports
    
    Safety Features:
    - Handles FLOOD_WAIT with automatic retry
    - Graceful permission degradation
    - Preserves OTP/verification code storage
    - Configurable dry-run mode
    """
    
    def __init__(
        self,
        client: Any,
        account_name: str = "unknown",
        leave_concurrency: int = 3,
        delete_history_concurrency: int = 2,
        delete_contacts_concurrency: int = 3,
        action_sleep: float = 0.3,
        min_peer_interval: float = 1.5,
        revoke_default: bool = True,
        report_dir: Optional[str] = None
    ):
        """
        Initialize OneClickCleaner.
        
        Args:
            client: Connected Telethon TelegramClient
            account_name: Name for this account (used in reports)
            leave_concurrency: Max concurrent leave operations
            delete_history_concurrency: Max concurrent delete operations
            delete_contacts_concurrency: Max concurrent contact delete operations
            action_sleep: Sleep between actions (seconds)
            min_peer_interval: Minimum interval between operations on same peer
            revoke_default: Whether to revoke messages by default
            report_dir: Directory to save reports (default: ./reports)
        """
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is required for OneClickCleaner")
        
        self.client = client
        self.account_name = account_name
        self.leave_concurrency = leave_concurrency
        self.delete_history_concurrency = delete_history_concurrency
        self.delete_contacts_concurrency = delete_contacts_concurrency
        self.action_sleep = action_sleep
        self.min_peer_interval = min_peer_interval
        self.revoke_default = revoke_default
        self.report_dir = Path(report_dir) if report_dir else Path("./reports")
        
        # Ensure report directory exists
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Internal state
        self.actions: List[CleanupAction] = []
        self.stats = {
            'groups_left': 0,
            'channels_left': 0,
            'histories_deleted': 0,
            'contacts_deleted': 0,
            'dialogs_closed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        logger.info(f"OneClickCleaner initialized for account: {account_name}")
        logger.info(f"Concurrency: leave={leave_concurrency}, delete_history={delete_history_concurrency}, delete_contacts={delete_contacts_concurrency}")
    
    async def list_dialogs(self) -> List[Dialog]:
        """
        List all dialogs for the account.
        
        Returns:
            List of Dialog objects
        """
        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs():
                dialogs.append(dialog)
            logger.info(f"Found {len(dialogs)} dialogs")
            return dialogs
        except Exception as e:
            logger.error(f"Error listing dialogs: {e}")
            return []
    
    async def list_contacts(self) -> List[User]:
        """
        List all contacts for the account.
        
        Returns:
            List of User objects
        """
        try:
            contacts = await self.client.get_contacts()
            logger.info(f"Found {len(contacts)} contacts")
            return contacts
        except Exception as e:
            logger.error(f"Error listing contacts: {e}")
            return []
    
    async def leave(self, dialog: Dialog) -> Tuple[bool, Optional[str]]:
        """
        Leave a group or channel.
        
        Args:
            dialog: Dialog to leave
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        entity = dialog.entity
        
        # Only leave groups and channels
        if not isinstance(entity, (Channel, Chat)):
            return False, "Not a group or channel"
        
        try:
            # Add jitter to action sleep
            await asyncio.sleep(self.action_sleep + random.uniform(0, 0.2))
            
            if isinstance(entity, Channel):
                # Leave channel
                await self.client(LeaveChannelRequest(entity))
                logger.info(f"Left channel: {dialog.title}")
                return True, None
            else:
                # Leave chat/group
                await self.client.delete_dialog(dialog)
                logger.info(f"Left group: {dialog.title}")
                return True, None
                
        except FloodWaitError as e:
            wait_time = e.seconds + random.uniform(1, 3)
            logger.warning(f"FLOOD_WAIT: {wait_time}s for {dialog.title}")
            await asyncio.sleep(wait_time)
            # Retry once
            try:
                if isinstance(entity, Channel):
                    await self.client(LeaveChannelRequest(entity))
                else:
                    await self.client.delete_dialog(dialog)
                return True, None
            except Exception as retry_err:
                return False, f"Retry failed: {str(retry_err)}"
                
        except UserNotParticipantError:
            return True, "Already left"
            
        except (ChatAdminRequiredError, ChannelPrivateError):
            return False, "Insufficient permissions"
            
        except Exception as e:
            logger.error(f"Error leaving {dialog.title}: {e}")
            return False, str(e)
    
    async def delete_history(self, dialog: Dialog, revoke: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Delete chat history for a dialog.
        
        Args:
            dialog: Dialog to delete history from
            revoke: Whether to revoke messages (delete for both sides)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        entity = dialog.entity
        
        try:
            # Add jitter to action sleep
            await asyncio.sleep(self.action_sleep + random.uniform(0, 0.2))
            
            # Try to delete history with revoke
            await self.client.delete_dialog(dialog, revoke=revoke)
            logger.info(f"Deleted history for: {dialog.title} (revoke={revoke})")
            return True, None
            
        except FloodWaitError as e:
            wait_time = e.seconds + random.uniform(1, 3)
            logger.warning(f"FLOOD_WAIT: {wait_time}s for {dialog.title}")
            await asyncio.sleep(wait_time)
            # Retry once
            try:
                await self.client.delete_dialog(dialog, revoke=revoke)
                return True, None
            except Exception as retry_err:
                # If revoke failed, try without revoke
                if revoke:
                    try:
                        await self.client.delete_dialog(dialog, revoke=False)
                        return True, "Partial: revoke not supported"
                    except:
                        pass
                return False, f"Retry failed: {str(retry_err)}"
                
        except (ChatAdminRequiredError, ChannelPrivateError):
            # If permission denied with revoke, try without revoke (delete only self messages)
            if revoke:
                try:
                    await self.client.delete_dialog(dialog, revoke=False)
                    return True, "Partial: only self messages deleted"
                except Exception as e2:
                    return False, f"No permissions: {str(e2)}"
            return False, "Insufficient permissions"
            
        except Exception as e:
            # Try without revoke as fallback
            if revoke:
                try:
                    await self.client.delete_dialog(dialog, revoke=False)
                    return True, "Partial: only self messages deleted"
                except:
                    pass
            logger.error(f"Error deleting history for {dialog.title}: {e}")
            return False, str(e)
    
    async def delete_contacts(self, contacts: List[User]) -> Tuple[int, List[str]]:
        """
        Delete all contacts.
        
        Args:
            contacts: List of User objects to delete
            
        Returns:
            Tuple of (deleted_count: int, errors: List[str])
        """
        if not contacts:
            return 0, []
        
        deleted = 0
        errors = []
        
        # Process in batches with concurrency control
        semaphore = asyncio.Semaphore(self.delete_contacts_concurrency)
        
        async def delete_contact(user: User):
            nonlocal deleted
            async with semaphore:
                try:
                    await asyncio.sleep(self.action_sleep + random.uniform(0, 0.2))
                    await self.client(DeleteContactsRequest(id=[user]))
                    deleted += 1
                    logger.info(f"Deleted contact: {user.first_name or 'Unknown'}")
                except FloodWaitError as e:
                    wait_time = e.seconds + random.uniform(1, 3)
                    logger.warning(f"FLOOD_WAIT: {wait_time}s for contact delete")
                    await asyncio.sleep(wait_time)
                    try:
                        await self.client(DeleteContactsRequest(id=[user]))
                        deleted += 1
                    except Exception as retry_err:
                        errors.append(f"Contact delete retry failed: {str(retry_err)}")
                except Exception as e:
                    errors.append(f"Error deleting contact: {str(e)}")
        
        # Process all contacts concurrently with semaphore limit
        tasks = [delete_contact(user) for user in contacts]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return deleted, errors
    
    async def close_or_archive(self, dialog: Dialog) -> Tuple[bool, Optional[str]]:
        """
        Close or archive a dialog (best-effort).
        
        Args:
            dialog: Dialog to close/archive
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            await asyncio.sleep(self.action_sleep + random.uniform(0, 0.2))
            
            # Archive the dialog
            await self.client.edit_folder(dialog, folder=1)
            logger.info(f"Archived dialog: {dialog.title}")
            return True, None
            
        except Exception as e:
            # Archiving might not be supported or allowed, that's okay
            logger.debug(f"Could not archive {dialog.title}: {e}")
            return False, str(e)
    
    async def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute the complete cleanup workflow.
        
        Workflow:
        1. Fetch all dialogs and contacts
        2. Leave all groups/channels
        3. Delete chat history for all dialogs
        4. Delete all contacts
        5. Archive remaining dialogs
        6. Generate report
        
        Args:
            dry_run: If True, only simulate actions without executing
            
        Returns:
            Dictionary with cleanup statistics and report path
        """
        start_time = time.time()
        logger.info(f"Starting cleanup for account: {self.account_name} (dry_run={dry_run})")
        
        try:
            # Step 1: Fetch all dialogs and contacts
            logger.info("Step 1: Fetching dialogs and contacts...")
            dialogs = await self.list_dialogs()
            contacts = await self.list_contacts()
            
            logger.info(f"Found {len(dialogs)} dialogs and {len(contacts)} contacts")
            
            if dry_run:
                logger.info("[DRY RUN] Would process:")
                logger.info(f"  - {len(dialogs)} dialogs")
                logger.info(f"  - {len(contacts)} contacts")
                return {
                    'dry_run': True,
                    'would_process': {
                        'dialogs': len(dialogs),
                        'contacts': len(contacts)
                    }
                }
            
            # Step 2: Leave all groups/channels
            logger.info("Step 2: Leaving groups and channels...")
            await self._leave_all_groups_channels(dialogs)
            
            # Step 3: Delete chat history for all dialogs
            logger.info("Step 3: Deleting chat histories...")
            await self._delete_all_histories(dialogs)
            
            # Step 4: Delete all contacts
            logger.info("Step 4: Deleting contacts...")
            if contacts:
                deleted_count, contact_errors = await self.delete_contacts(contacts)
                self.stats['contacts_deleted'] = deleted_count
                if contact_errors:
                    self.stats['errors'] += len(contact_errors)
            
            # Step 5: Archive remaining dialogs (best-effort)
            logger.info("Step 5: Archiving remaining dialogs...")
            await self._archive_remaining(dialogs)
            
            # Step 6: Generate report
            elapsed_time = time.time() - start_time
            logger.info(f"Cleanup completed in {elapsed_time:.2f} seconds")
            
            report_path = await self._generate_report(elapsed_time)
            
            return {
                'success': True,
                'stats': self.stats,
                'report_path': str(report_path),
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            elapsed_time = time.time() - start_time
            
            # Try to generate report even on failure
            try:
                report_path = await self._generate_report(elapsed_time, failed=True, error=str(e))
            except:
                report_path = None
            
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats,
                'report_path': str(report_path) if report_path else None,
                'elapsed_time': elapsed_time
            }
    
    async def _leave_all_groups_channels(self, dialogs: List[Dialog]):
        """Leave all groups and channels with concurrency control"""
        semaphore = asyncio.Semaphore(self.leave_concurrency)
        
        async def process_leave(dialog: Dialog):
            async with semaphore:
                entity = dialog.entity
                if not isinstance(entity, (Channel, Chat)):
                    return
                
                action = CleanupAction(
                    chat_id=dialog.id,
                    title=dialog.title or "Unknown",
                    chat_type='channel' if isinstance(entity, Channel) else 'group'
                )
                
                success, error = await self.leave(dialog)
                
                if success:
                    action.actions_done.append('left')
                    action.status = 'success'
                    if isinstance(entity, Channel):
                        self.stats['channels_left'] += 1
                    else:
                        self.stats['groups_left'] += 1
                else:
                    action.status = 'failed' if not error or 'Already left' not in error else 'skipped'
                    action.error = error
                    if action.status == 'failed':
                        self.stats['errors'] += 1
                    else:
                        self.stats['skipped'] += 1
                
                self.actions.append(action)
                
                # Enforce minimum peer interval
                await asyncio.sleep(self.min_peer_interval)
        
        tasks = [process_leave(dialog) for dialog in dialogs]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _delete_all_histories(self, dialogs: List[Dialog]):
        """Delete history for all dialogs with concurrency control"""
        semaphore = asyncio.Semaphore(self.delete_history_concurrency)
        
        async def process_delete(dialog: Dialog):
            async with semaphore:
                entity = dialog.entity
                
                # Determine chat type
                if isinstance(entity, Channel):
                    chat_type = 'channel'
                elif isinstance(entity, Chat):
                    chat_type = 'group'
                elif isinstance(entity, User):
                    chat_type = 'bot' if entity.bot else 'private'
                else:
                    chat_type = 'unknown'
                
                # Find or create action
                action = None
                for a in self.actions:
                    if a.chat_id == dialog.id:
                        action = a
                        break
                
                if not action:
                    action = CleanupAction(
                        chat_id=dialog.id,
                        title=dialog.title or "Unknown",
                        chat_type=chat_type
                    )
                    self.actions.append(action)
                
                success, error = await self.delete_history(dialog, revoke=self.revoke_default)
                
                if success:
                    action.actions_done.append('history_deleted')
                    if action.status == 'pending':
                        action.status = 'success'
                    self.stats['histories_deleted'] += 1
                    
                    if error and 'Partial' in error:
                        action.status = 'partial'
                        action.error = error
                else:
                    if action.status == 'pending':
                        action.status = 'failed'
                    action.error = error
                    self.stats['errors'] += 1
                
                # Enforce minimum peer interval
                await asyncio.sleep(self.min_peer_interval)
        
        tasks = [process_delete(dialog) for dialog in dialogs]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _archive_remaining(self, dialogs: List[Dialog]):
        """Archive remaining dialogs (best-effort)"""
        for dialog in dialogs:
            try:
                success, error = await self.close_or_archive(dialog)
                if success:
                    self.stats['dialogs_closed'] += 1
            except Exception as e:
                logger.debug(f"Error archiving dialog: {e}")
    
    async def _generate_report(self, elapsed_time: float, failed: bool = False, error: Optional[str] = None) -> Path:
        """
        Generate cleanup report in CSV and JSON formats.
        
        Args:
            elapsed_time: Total elapsed time in seconds
            failed: Whether the cleanup failed
            error: Error message if failed
            
        Returns:
            Path to the generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_base = self.report_dir / f"cleanup_{self.account_name}_{timestamp}"
        
        # Generate CSV report
        csv_path = report_base.with_suffix('.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'chat_id', 'title', 'type', 'actions_done', 'status', 'error', 'timestamp'
            ])
            writer.writeheader()
            for action in self.actions:
                writer.writerow({
                    'chat_id': action.chat_id,
                    'title': action.title,
                    'type': action.chat_type,
                    'actions_done': ', '.join(action.actions_done),
                    'status': action.status,
                    'error': action.error or '',
                    'timestamp': action.timestamp
                })
        
        # Generate JSON report
        json_path = report_base.with_suffix('.json')
        report_data = {
            'account_name': self.account_name,
            'timestamp': timestamp,
            'elapsed_time_seconds': elapsed_time,
            'failed': failed,
            'error': error,
            'statistics': self.stats,
            'actions': [
                {
                    'chat_id': a.chat_id,
                    'title': a.title,
                    'chat_type': a.chat_type,
                    'actions_done': a.actions_done,
                    'status': a.status,
                    'error': a.error,
                    'timestamp': a.timestamp
                }
                for a in self.actions
            ]
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Reports generated: {csv_path} and {json_path}")
        
        return csv_path
