#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Registration Time Checker
获取 Telegram 官方显示的注册时间
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from telethon import TelegramClient
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.errors import (
        FloodWaitError, 
        UserPrivacyRestrictedError,
        RPCError
    )
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("❌ telethon未安装，注册时间查询功能不可用")

logger = logging.getLogger(__name__)


@dataclass
class RegistrationInfo:
    """账号注册信息"""
    user_id: int
    username: Optional[str]
    phone: Optional[str]
    first_name: str
    last_name: Optional[str]
    common_chats_count: int
    about: Optional[str]
    # Telegram doesn't expose exact registration date via API
    # We can only estimate based on user ID ranges
    estimated_year: Optional[int] = None
    estimated_month: Optional[int] = None
    user_id_range: Optional[str] = None
    error: Optional[str] = None


class RegistrationChecker:
    """
    Telegram账号注册时间检查器
    注意：Telegram官方API不直接提供注册时间
    我们使用user_id范围来估算注册时期
    """
    
    # User ID ranges for different time periods (approximate)
    # Based on Telegram's user ID allocation over time
    USER_ID_RANGES = [
        (0, 10000000, 2013, "Early Adopters"),
        (10000000, 50000000, 2014, "2014 Wave"),
        (50000000, 150000000, 2015, "2015 Wave"),
        (150000000, 300000000, 2016, "2016 Wave"),
        (300000000, 500000000, 2017, "2017 Wave"),
        (500000000, 800000000, 2018, "2018 Wave"),
        (800000000, 1200000000, 2019, "2019 Wave"),
        (1200000000, 1700000000, 2020, "2020 Wave"),
        (1700000000, 2300000000, 2021, "2021 Wave"),
        (2300000000, 3000000000, 2022, "2022 Wave"),
        (3000000000, 4000000000, 2023, "2023 Wave"),
        (4000000000, 5000000000, 2024, "2024 Wave"),
        (5000000000, 10000000000, 2025, "Recent Users"),
    ]
    
    def __init__(self, api_id: int, api_hash: str, session_path: str = None, proxy: Dict = None):
        """
        初始化注册时间检查器
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_path: Session文件路径（可选）
            proxy: 代理配置（可选）
        """
        if not TELETHON_AVAILABLE:
            raise ImportError("telethon is required for RegistrationChecker")
        
        self.api_id = int(api_id)
        self.api_hash = str(api_hash)
        self.session_path = session_path or "registration_checker"
        self.proxy = proxy
        self.client = None
    
    async def connect(self):
        """连接到Telegram"""
        if self.client and self.client.is_connected():
            return
        
        self.client = TelegramClient(
            self.session_path,
            self.api_id,
            self.api_hash,
            proxy=self.proxy
        )
        
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            raise RuntimeError("Session未授权，请先登录")
        
        logger.info("✅ 已连接到Telegram")
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            logger.info("👋 已断开连接")
    
    def estimate_registration_period(self, user_id: int) -> Tuple[int, str]:
        """
        根据user_id估算注册时期
        
        Args:
            user_id: Telegram用户ID
        
        Returns:
            (年份, 描述) 元组
        """
        for min_id, max_id, year, description in self.USER_ID_RANGES:
            if min_id <= user_id < max_id:
                return year, description
        
        # 如果超出范围，返回最新
        return 2025, "Unknown Period"
    
    async def get_registration_info(self, user_id_or_username) -> RegistrationInfo:
        """
        获取用户的注册信息
        
        Args:
            user_id_or_username: 用户ID或用户名
        
        Returns:
            RegistrationInfo对象
        """
        try:
            # 确保已连接
            await self.connect()
            
            # 获取用户基本信息
            user = await self.client.get_entity(user_id_or_username)
            
            logger.info(f"📱 用户ID: {user.id}")
            logger.info(f"   用户名: @{user.username if user.username else 'N/A'}")
            logger.info(f"   名字: {user.first_name} {user.last_name or ''}")
            
            # 获取完整信息
            full = await self.client(GetFullUserRequest(user.id))
            full_user = full.full_user
            
            # 提取信息
            common_chats = getattr(full_user, 'common_chats_count', 0)
            about = getattr(full_user, 'about', None)
            
            # 估算注册时期
            estimated_year, range_desc = self.estimate_registration_period(user.id)
            
            logger.info(f"   共同群组: {common_chats}")
            logger.info(f"   个人简介: {about[:50] if about else 'N/A'}")
            logger.info(f"   估算注册: {estimated_year} ({range_desc})")
            
            return RegistrationInfo(
                user_id=user.id,
                username=user.username,
                phone=user.phone if hasattr(user, 'phone') else None,
                first_name=user.first_name,
                last_name=user.last_name,
                common_chats_count=common_chats,
                about=about,
                estimated_year=estimated_year,
                user_id_range=range_desc
            )
            
        except UserPrivacyRestrictedError:
            logger.warning(f"❌ 隐私设置限制，无法获取 {user_id_or_username} 的信息")
            return RegistrationInfo(
                user_id=0,
                username=None,
                phone=None,
                first_name="",
                last_name=None,
                common_chats_count=0,
                about=None,
                error="隐私设置限制"
            )
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ 请求过于频繁，需要等待 {e.seconds} 秒")
            return RegistrationInfo(
                user_id=0,
                username=None,
                phone=None,
                first_name="",
                last_name=None,
                common_chats_count=0,
                about=None,
                error=f"需要等待 {e.seconds} 秒"
            )
            
        except Exception as e:
            logger.error(f"❌ 获取信息失败: {e}")
            import traceback
            traceback.print_exc()
            return RegistrationInfo(
                user_id=0,
                username=None,
                phone=None,
                first_name="",
                last_name=None,
                common_chats_count=0,
                about=None,
                error=str(e)
            )
    
    async def check_multiple_accounts(
        self, 
        session_files: List[str],
        progress_callback=None
    ) -> List[RegistrationInfo]:
        """
        批量检查多个账号的注册信息
        
        Args:
            session_files: Session文件路径列表
            progress_callback: 进度回调函数
        
        Returns:
            RegistrationInfo列表
        """
        results = []
        total = len(session_files)
        
        for idx, session_file in enumerate(session_files):
            try:
                logger.info(f"📊 检查账号 {idx + 1}/{total}: {session_file}")
                
                # 为每个session创建独立的客户端
                temp_client = TelegramClient(
                    session_file,
                    self.api_id,
                    self.api_hash,
                    proxy=self.proxy
                )
                
                await temp_client.connect()
                
                if not await temp_client.is_user_authorized():
                    logger.warning(f"⚠️ Session未授权: {session_file}")
                    results.append(RegistrationInfo(
                        user_id=0,
                        username=None,
                        phone=None,
                        first_name=session_file,
                        last_name=None,
                        common_chats_count=0,
                        about=None,
                        error="Session未授权"
                    ))
                    await temp_client.disconnect()
                    continue
                
                # 获取自己的信息
                me = await temp_client.get_me()
                
                # 获取完整信息
                full = await temp_client(GetFullUserRequest(me.id))
                full_user = full.full_user
                
                common_chats = getattr(full_user, 'common_chats_count', 0)
                about = getattr(full_user, 'about', None)
                estimated_year, range_desc = self.estimate_registration_period(me.id)
                
                info = RegistrationInfo(
                    user_id=me.id,
                    username=me.username,
                    phone=me.phone if hasattr(me, 'phone') else None,
                    first_name=me.first_name,
                    last_name=me.last_name,
                    common_chats_count=common_chats,
                    about=about,
                    estimated_year=estimated_year,
                    user_id_range=range_desc
                )
                
                results.append(info)
                
                await temp_client.disconnect()
                
                # 调用进度回调
                if progress_callback:
                    await progress_callback(idx + 1, total, info)
                
                # 避免频繁请求
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ 检查失败 {session_file}: {e}")
                results.append(RegistrationInfo(
                    user_id=0,
                    username=None,
                    phone=None,
                    first_name=session_file,
                    last_name=None,
                    common_chats_count=0,
                    about=None,
                    error=str(e)
                ))
        
        return results


class AccountClassifierByRegistration:
    """按注册时间分类账号"""
    
    @staticmethod
    def classify_by_year(accounts: List[RegistrationInfo]) -> Dict[int, List[RegistrationInfo]]:
        """按年份分类"""
        classified = {}
        
        for account in accounts:
            if account.error:
                year = 0  # 错误账号
            else:
                year = account.estimated_year or 0
            
            if year not in classified:
                classified[year] = []
            classified[year].append(account)
        
        return dict(sorted(classified.items()))
    
    @staticmethod
    def classify_by_user_id_range(accounts: List[RegistrationInfo]) -> Dict[str, List[RegistrationInfo]]:
        """按用户ID范围分类"""
        classified = {}
        
        for account in accounts:
            if account.error:
                range_key = "错误账号"
            else:
                range_key = account.user_id_range or "未知"
            
            if range_key not in classified:
                classified[range_key] = []
            classified[range_key].append(account)
        
        return classified
    
    @staticmethod
    def generate_report(accounts: List[RegistrationInfo]) -> str:
        """生成分类报告"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Telegram账号注册时间分析报告")
        report_lines.append("=" * 80)
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"总账号数: {len(accounts)}")
        report_lines.append("")
        
        # 按年份统计
        by_year = AccountClassifierByRegistration.classify_by_year(accounts)
        report_lines.append("【按年份分类】")
        report_lines.append("-" * 80)
        for year, accs in by_year.items():
            year_label = f"{year}年" if year > 0 else "错误/未知"
            report_lines.append(f"{year_label}: {len(accs)} 个账号")
        report_lines.append("")
        
        # 按用户ID范围统计
        by_range = AccountClassifierByRegistration.classify_by_user_id_range(accounts)
        report_lines.append("【按时期分类】")
        report_lines.append("-" * 80)
        for range_key, accs in by_range.items():
            report_lines.append(f"{range_key}: {len(accs)} 个账号")
        report_lines.append("")
        
        # 详细信息
        report_lines.append("【详细账号信息】")
        report_lines.append("-" * 80)
        for idx, account in enumerate(accounts, 1):
            report_lines.append(f"\n{idx}. 账号信息:")
            if account.error:
                report_lines.append(f"   ❌ 错误: {account.error}")
                report_lines.append(f"   文件: {account.first_name}")
            else:
                report_lines.append(f"   用户ID: {account.user_id}")
                report_lines.append(f"   用户名: @{account.username if account.username else 'N/A'}")
                report_lines.append(f"   手机号: {account.phone if account.phone else 'N/A'}")
                report_lines.append(f"   名字: {account.first_name} {account.last_name or ''}")
                report_lines.append(f"   估算注册: {account.estimated_year}年 ({account.user_id_range})")
                report_lines.append(f"   共同群组: {account.common_chats_count}")
                if account.about:
                    about_preview = account.about[:100] + "..." if len(account.about) > 100 else account.about
                    report_lines.append(f"   个人简介: {about_preview}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        report_lines.append("注意：注册时间是基于用户ID范围的估算值")
        report_lines.append("Telegram官方API不直接提供准确的注册日期")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


# 示例用法
async def example_usage():
    """示例：如何使用注册时间检查器"""
    
    # 从环境变量获取API凭据
    import os
    api_id = int(os.getenv('API_ID', '0'))
    api_hash = os.getenv('API_HASH', '')
    
    if not api_id or not api_hash:
        print("请设置 API_ID 和 API_HASH 环境变量")
        return
    
    # 创建检查器
    checker = RegistrationChecker(
        api_id=api_id,
        api_hash=api_hash,
        session_path="my_session"
    )
    
    try:
        # 连接
        await checker.connect()
        
        # 查询单个用户
        info = await checker.get_registration_info("username_or_id")
        print(f"\n用户信息:")
        print(f"  ID: {info.user_id}")
        print(f"  估算注册: {info.estimated_year}年")
        print(f"  时期: {info.user_id_range}")
        
    finally:
        await checker.disconnect()


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
