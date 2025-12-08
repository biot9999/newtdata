#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
One-Click Cleanup Service for Telegram Accounts

This service provides comprehensive cleanup functionality for Telegram accounts:
- Leave all groups and channels
- Delete chat history (with optional revoke for two-way deletion)
- Remove all contacts
- Archive remaining dialogs
- Generate detailed reports in CSV and JSON formats

Author: Telegram Account Management Bot
Version: 1.0
"""

import asyncio
import logging
import time
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, ChatWriteForbiddenError, ChatAdminRequiredError,
    UserBannedInChannelError, ChannelPrivateError, PeerIdInvalidError,
    MessageDeleteForbiddenError, RPCError
)
from telethon.tl.types import (
    User, Chat, Channel, Dialog,
    PeerUser, PeerChat, PeerChannel
)
from telethon.tl.functions.messages import (
    DeleteHistoryRequest, DeleteChatUserRequest
)
from telethon.tl.functions.channels import (
    LeaveChannelRequest, DeleteHistoryRequest as ChannelDeleteHistoryRequest
)
from telethon.tl.functions.contacts import (
    DeleteContactsRequest, GetContactsRequest
)

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class CleanupAction:
    """Record of a single cleanup action"""
    chat_id: int
    title: str
    chat_type: str  # 'user', 'group', 'channel', 'bot'
    actions_done: List[str] = field(default_factory=list)
    status: str = 'pending'  # 'pending', 'success', 'partial', 'failed', 'skipped'
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CleanupReport:
    """Complete cleanup report for an account"""
    account_name: str
    timestamp: str
    elapsed_time_seconds: float
    statistics: Dict[str, int] = field(default_factory=dict)
    actions: List[CleanupAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        return {
            'account_name': self.account_name,
            'timestamp': self.timestamp,
            'elapsed_time_seconds': round(self.elapsed_time_seconds, 2),
            'statistics': self.statistics,
            'actions': [asdict(action) for action in self.actions]
        }


class OneClickCleaner:
    """
    One-Click Cleanup Service
    
    Provides comprehensive cleanup functionality for Telegram accounts with:
    - Concurrent operations with rate limiting
    - Automatic FLOOD_WAIT handling
    - Detailed reporting
    - Safe error handling
    """
    
    def __init__(
        self,
        client: TelegramClient,
        account_name: str,
        leave_concurrency: int = 3,
        delete_history_concurrency: int = 2,
        delete_contacts_concurrency: int = 3,
        action_sleep: float = 0.3,
        min_peer_interval: float = 1.5,
        revoke_default: bool = True,
        report_dir: Optional[str] = None
    ):
        """
        Initialize OneClickCleaner
        
        Args:
            client: Connected TelegramClient instance
            account_name: Name/identifier for this account
            leave_concurrency: Max concurrent leave operations
            delete_history_concurrency: Max concurrent delete history operations
            delete_contacts_concurrency: Max concurrent contact deletion operations
            action_sleep: Sleep time between actions (seconds)
            min_peer_interval: Minimum interval between operations on same peer
            revoke_default: Whether to revoke messages by default (two-way deletion)
            report_dir: Directory to save reports (default: './results/cleanup_reports')
        """
        self.client = client
        self.account_name = account_name
        self.leave_concurrency = leave_concurrency
        self.delete_history_concurrency = delete_history_concurrency
        self.delete_contacts_concurrency = delete_contacts_concurrency
        self.action_sleep = action_sleep
        self.min_peer_interval = min_peer_interval
        self.revoke_default = revoke_default
        
        # Setup report directory
        if report_dir:
            self.report_dir = Path(report_dir)
        else:
            self.report_dir = Path('./results/cleanup_reports')
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'groups_left': 0,
            'channels_left': 0,
            'histories_deleted': 0,
            'contacts_deleted': 0,
            'dialogs_closed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        # Actions log
        self.actions: List[CleanupAction] = []
        
        # Rate limiting
        self.last_action_time: Dict[int, float] = {}
        self.leave_semaphore = asyncio.Semaphore(leave_concurrency)
        self.delete_semaphore = asyncio.Semaphore(delete_history_concurrency)
        self.contacts_semaphore = asyncio.Semaphore(delete_contacts_concurrency)
        
        logger.info(f"OneClickCleaner initialized for account: {account_name}")
    
    async def run(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute complete cleanup process
        
        Args:
            dry_run: If True, only simulate actions without executing
            
        Returns:
            Dictionary with cleanup results and report path
        """
        start_time = time.time()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Starting cleanup for {self.account_name} (dry_run={dry_run})")
        
        try:
            # Step 1: Get all dialogs
            logger.info("Fetching dialogs...")
            dialogs = await self.client.get_dialogs()
            logger.info(f"Found {len(dialogs)} dialogs")
            
            # Categorize dialogs
            groups = []
            channels = []
            users = []
            bots = []
            
            for dialog in dialogs:
                entity = dialog.entity
                if isinstance(entity, Channel):
                    if entity.broadcast:
                        channels.append(dialog)
                    else:
                        groups.append(dialog)
                elif isinstance(entity, Chat):
                    groups.append(dialog)
                elif isinstance(entity, User):
                    if entity.bot:
                        bots.append(dialog)
                    else:
                        users.append(dialog)
            
            logger.info(f"Categorized: {len(groups)} groups, {len(channels)} channels, "
                       f"{len(users)} users, {len(bots)} bots")
            
            # Step 2: Leave groups and channels
            if not dry_run:
                logger.info("Leaving groups and channels...")
                await self._leave_groups_and_channels(groups, channels)
            else:
                logger.info(f"[DRY RUN] Would leave {len(groups)} groups and {len(channels)} channels")
            
            # Step 3: Delete chat history
            if not dry_run:
                logger.info("Deleting chat histories...")
                await self._delete_chat_histories(users + bots)
            else:
                logger.info(f"[DRY RUN] Would delete history for {len(users) + len(bots)} chats")
            
            # Step 4: Delete contacts
            if not dry_run:
                logger.info("Deleting contacts...")
                await self._delete_contacts()
            else:
                logger.info("[DRY RUN] Would delete all contacts")
            
            # Step 5: Archive remaining dialogs
            if not dry_run:
                logger.info("Archiving remaining dialogs...")
                await self._archive_remaining_dialogs()
            else:
                logger.info("[DRY RUN] Would archive remaining dialogs")
            
            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            
            # Generate report
            report = CleanupReport(
                account_name=self.account_name,
                timestamp=timestamp,
                elapsed_time_seconds=elapsed_time,
                statistics=self.stats.copy(),
                actions=self.actions.copy()
            )
            
            # Save reports
            csv_path = self.report_dir / f"cleanup_{self.account_name}_{timestamp}.csv"
            json_path = self.report_dir / f"cleanup_{self.account_name}_{timestamp}.json"
            
            self._save_csv_report(report, csv_path)
            self._save_json_report(report, json_path)
            
            logger.info(f"Cleanup completed in {elapsed_time:.2f}s")
            logger.info(f"Reports saved: {csv_path}, {json_path}")
            
            return {
                'success': True,
                'elapsed_time': elapsed_time,
                'statistics': self.stats,
                'report_path': str(json_path),
                'csv_path': str(csv_path)
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'statistics': self.stats
            }
    
    async def _leave_groups_and_channels(self, groups: List[Dialog], channels: List[Dialog]):
        """Leave all groups and channels with rate limiting"""
        all_entities = groups + channels
        
        tasks = []
        for dialog in all_entities:
            task = self._leave_single_entity(dialog)
            tasks.append(task)
        
        # Execute with concurrency control
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _leave_single_entity(self, dialog: Dialog):
        """Leave a single group or channel"""
        async with self.leave_semaphore:
            entity = dialog.entity
            chat_id = entity.id
            title = getattr(entity, 'title', 'Unknown')
            
            # Determine chat type
            if isinstance(entity, Channel):
                chat_type = 'channel' if entity.broadcast else 'group'
            else:
                chat_type = 'group'
            
            action = CleanupAction(
                chat_id=chat_id,
                title=title,
                chat_type=chat_type
            )
            
            try:
                # Rate limiting
                await self._wait_for_rate_limit(chat_id)
                
                # Leave the entity
                if isinstance(entity, Channel):
                    await self.client(LeaveChannelRequest(entity))
                else:
                    # For regular groups, delete chat user (self)
                    me = await self.client.get_me()
                    await self.client(DeleteChatUserRequest(chat_id, me))
                
                action.actions_done.append('left')
                action.status = 'success'
                
                if chat_type == 'channel':
                    self.stats['channels_left'] += 1
                else:
                    self.stats['groups_left'] += 1
                
                logger.debug(f"Left {chat_type}: {title}")
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"FloodWait when leaving {title}: {wait_time}s")
                await asyncio.sleep(wait_time)
                # Retry once
                try:
                    if isinstance(entity, Channel):
                        await self.client(LeaveChannelRequest(entity))
                    else:
                        me = await self.client.get_me()
                        await self.client(DeleteChatUserRequest(chat_id, me))
                    action.actions_done.append('left')
                    action.status = 'success'
                    if chat_type == 'channel':
                        self.stats['channels_left'] += 1
                    else:
                        self.stats['groups_left'] += 1
                except Exception as retry_error:
                    action.status = 'failed'
                    action.error = f"Retry failed: {str(retry_error)}"
                    self.stats['errors'] += 1
                    logger.error(f"Retry failed for {title}: {retry_error}")
                    
            except (ChatAdminRequiredError, UserBannedInChannelError, ChannelPrivateError) as e:
                action.status = 'failed'
                action.error = f"Permission error: {type(e).__name__}"
                self.stats['errors'] += 1
                logger.warning(f"Cannot leave {title}: {type(e).__name__}")
                
            except Exception as e:
                action.status = 'failed'
                action.error = str(e)
                self.stats['errors'] += 1
                logger.error(f"Error leaving {title}: {e}")
            
            finally:
                self.actions.append(action)
                await asyncio.sleep(self.action_sleep)
    
    async def _delete_chat_histories(self, dialogs: List[Dialog]):
        """Delete chat histories for all dialogs"""
        tasks = []
        for dialog in dialogs:
            task = self._delete_single_history(dialog)
            tasks.append(task)
        
        # Execute with concurrency control
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _delete_single_history(self, dialog: Dialog):
        """Delete history for a single chat"""
        async with self.delete_semaphore:
            entity = dialog.entity
            chat_id = entity.id
            # Get title with proper fallback chain
            if hasattr(entity, 'first_name') and entity.first_name:
                title = entity.first_name
            elif hasattr(entity, 'username') and entity.username:
                title = entity.username
            else:
                title = 'Unknown'
            
            # Determine chat type
            if isinstance(entity, User):
                chat_type = 'bot' if entity.bot else 'user'
            else:
                chat_type = 'chat'
            
            action = CleanupAction(
                chat_id=chat_id,
                title=title,
                chat_type=chat_type
            )
            
            try:
                # Rate limiting
                await self._wait_for_rate_limit(chat_id)
                
                # Try to delete with revoke (two-way deletion)
                if self.revoke_default:
                    try:
                        await self.client(DeleteHistoryRequest(
                            peer=entity,
                            max_id=0,
                            just_clear=False,
                            revoke=True
                        ))
                        action.actions_done.append('history_deleted')
                        action.actions_done.append('revoked')
                        action.status = 'success'
                        self.stats['histories_deleted'] += 1
                        logger.debug(f"Deleted history (revoked) for: {title}")
                        
                    except (ChatWriteForbiddenError, MessageDeleteForbiddenError):
                        # Fall back to one-way deletion
                        await self.client(DeleteHistoryRequest(
                            peer=entity,
                            max_id=0,
                            just_clear=False,
                            revoke=False
                        ))
                        action.actions_done.append('history_deleted')
                        action.status = 'partial'
                        action.error = 'Partial: only self messages deleted'
                        self.stats['histories_deleted'] += 1
                        logger.debug(f"Deleted history (one-way) for: {title}")
                else:
                    # One-way deletion only
                    await self.client(DeleteHistoryRequest(
                        peer=entity,
                        max_id=0,
                        just_clear=False,
                        revoke=False
                    ))
                    action.actions_done.append('history_deleted')
                    action.status = 'success'
                    self.stats['histories_deleted'] += 1
                    logger.debug(f"Deleted history for: {title}")
                
            except FloodWaitError as e:
                wait_time = e.seconds
                logger.warning(f"FloodWait when deleting history for {title}: {wait_time}s")
                await asyncio.sleep(wait_time)
                # Retry once
                try:
                    await self.client(DeleteHistoryRequest(
                        peer=entity,
                        max_id=0,
                        just_clear=False,
                        revoke=False
                    ))
                    action.actions_done.append('history_deleted')
                    action.status = 'success'
                    self.stats['histories_deleted'] += 1
                except Exception as retry_error:
                    action.status = 'failed'
                    action.error = f"Retry failed: {str(retry_error)}"
                    self.stats['errors'] += 1
                    logger.error(f"Retry failed for {title}: {retry_error}")
                    
            except PeerIdInvalidError:
                action.status = 'skipped'
                action.error = 'Invalid peer'
                self.stats['skipped'] += 1
                logger.debug(f"Skipped invalid peer: {title}")
                
            except Exception as e:
                action.status = 'failed'
                action.error = str(e)
                self.stats['errors'] += 1
                logger.error(f"Error deleting history for {title}: {e}")
            
            finally:
                self.actions.append(action)
                await asyncio.sleep(self.action_sleep)
    
    async def _delete_contacts(self):
        """Delete all contacts"""
        async with self.contacts_semaphore:
            try:
                # Get all contacts
                result = await self.client(GetContactsRequest(hash=0))
                
                if not hasattr(result, 'users') or not result.users:
                    logger.info("No contacts to delete")
                    return
                
                # Extract contact user IDs
                contact_ids = [user.id for user in result.users]
                
                logger.info(f"Deleting {len(contact_ids)} contacts...")
                
                # Delete contacts in batches (Telegram limits batch size)
                batch_size = 100
                for i in range(0, len(contact_ids), batch_size):
                    batch = contact_ids[i:i + batch_size]
                    
                    try:
                        await self.client(DeleteContactsRequest(id=batch))
                        self.stats['contacts_deleted'] += len(batch)
                        logger.debug(f"Deleted {len(batch)} contacts")
                        
                        # Rate limiting between batches
                        if i + batch_size < len(contact_ids):
                            await asyncio.sleep(self.action_sleep * 2)
                            
                    except FloodWaitError as e:
                        wait_time = e.seconds
                        logger.warning(f"FloodWait when deleting contacts: {wait_time}s")
                        await asyncio.sleep(wait_time)
                        # Retry this batch
                        try:
                            await self.client(DeleteContactsRequest(id=batch))
                            self.stats['contacts_deleted'] += len(batch)
                        except Exception as retry_error:
                            self.stats['errors'] += 1
                            logger.error(f"Retry failed for contact batch: {retry_error}")
                    
                    except Exception as e:
                        self.stats['errors'] += 1
                        logger.error(f"Error deleting contact batch: {e}")
                
                logger.info(f"Deleted {self.stats['contacts_deleted']} contacts")
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error getting/deleting contacts: {e}")
    
    async def _archive_remaining_dialogs(self):
        """Archive all remaining dialogs"""
        try:
            dialogs = await self.client.get_dialogs()
            
            archived_count = 0
            for dialog in dialogs:
                try:
                    # Archive the dialog
                    await self.client.edit_folder(dialog.entity, folder=1)
                    archived_count += 1
                    
                    # Rate limiting
                    await asyncio.sleep(self.action_sleep)
                    
                except FloodWaitError as e:
                    logger.warning(f"FloodWait when archiving: {e.seconds}s")
                    await asyncio.sleep(e.seconds)
                    try:
                        await self.client.edit_folder(dialog.entity, folder=1)
                        archived_count += 1
                    except Exception as archive_error:
                        # Silently ignore archive errors as they're not critical
                        logger.debug(f"Cannot archive dialog: {archive_error}")
                        pass
                        
                except Exception as e:
                    logger.debug(f"Cannot archive dialog: {e}")
            
            self.stats['dialogs_closed'] = archived_count
            logger.info(f"Archived {archived_count} dialogs")
            
        except Exception as e:
            logger.error(f"Error archiving dialogs: {e}")
    
    async def _wait_for_rate_limit(self, chat_id: int):
        """Wait if necessary to respect rate limits for a specific chat"""
        if chat_id in self.last_action_time:
            elapsed = time.time() - self.last_action_time[chat_id]
            if elapsed < self.min_peer_interval:
                await asyncio.sleep(self.min_peer_interval - elapsed)
        
        self.last_action_time[chat_id] = time.time()
    
    def _save_csv_report(self, report: CleanupReport, path: Path):
        """Save cleanup report as CSV"""
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'chat_id', 'title', 'type', 'actions_done', 
                    'status', 'error', 'timestamp'
                ])
                
                # Data rows
                for action in report.actions:
                    writer.writerow([
                        action.chat_id,
                        action.title,
                        action.chat_type,
                        ', '.join(action.actions_done),
                        action.status,
                        action.error or '',
                        action.timestamp
                    ])
            
            logger.info(f"CSV report saved: {path}")
            
        except Exception as e:
            logger.error(f"Error saving CSV report: {e}")
    
    def _save_json_report(self, report: CleanupReport, path: Path):
        """Save cleanup report as JSON"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON report saved: {path}")
            
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")


# Example usage
async def example_usage():
    """Example of how to use OneClickCleaner"""
    # This is just an example - actual usage is through the bot
    
    from telethon import TelegramClient
    import os
    
    # Use environment variables or placeholders
    api_id = int(os.getenv("API_ID", "0"))
    api_hash = os.getenv("API_HASH", "")
    session_path = "account.session"
    
    client = TelegramClient(session_path, api_id, api_hash)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("Session not authorized")
        return
    
    # Create cleaner instance
    cleaner = OneClickCleaner(
        client=client,
        account_name="account.session",
        leave_concurrency=3,
        delete_history_concurrency=2,
        delete_contacts_concurrency=3,
        action_sleep=0.3,
        min_peer_interval=1.5,
        revoke_default=True,
        report_dir="./reports"
    )
    
    # Run cleanup
    result = await cleaner.run(dry_run=False)
    
    print(f"Cleanup completed: {result}")
    
    await client.disconnect()


if __name__ == "__main__":
    # This module is meant to be imported, not run directly
    # But we provide an example for testing
    import asyncio
    asyncio.run(example_usage())
