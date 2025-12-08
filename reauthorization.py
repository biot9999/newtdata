#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新授权功能模块
Implements automatic re-authorization for Telegram accounts
"""

import os
import re
import json
import shutil
import asyncio
from typing import Optional, Dict, Tuple
from datetime import datetime

# 常量定义
REAUTH_TIMEOUT = 300  # 超时时间（秒）
CODE_ARRIVAL_WAIT = 5  # 验证码到达等待时间（秒）

try:
    from telethon import TelegramClient
    from telethon.tl.functions.auth import SendCodeRequest, ResetAuthorizationsRequest
    from telethon.tl.functions.account import GetAuthorizationsRequest
    from telethon.tl.types.auth import CodeSettings
    from telethon.errors import SessionPasswordNeededError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("⚠️ Telethon未安装，重新授权功能不可用")

try:
    from opentele.api import API, UseCurrentSession
    from opentele.td import TDesktop
    from opentele.tl import TelegramClient as OpenTeleClient
    OPENTELE_AVAILABLE = True
except ImportError:
    OPENTELE_AVAILABLE = False
    print("⚠️ opentele未安装，TData转换功能不可用")


class ReauthorizationManager:
    """重新授权管理器"""
    
    def __init__(self, api_id: int, api_hash: str):
        """
        初始化重新授权管理器
        
        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
        """
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is required for reauthorization")
        
        self.api_id = int(api_id)
        self.api_hash = str(api_hash)
    
    async def reset_sessions(self, client: TelegramClient) -> bool:
        """
        重置所有会话（踢掉其他设备）
        
        Args:
            client: 已登录的TelegramClient实例
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            # 获取当前账号的所有登录设备/会话
            sessions = await client(GetAuthorizationsRequest())
            
            # 如果有多个会话（说明在其他设备登录过）
            if len(sessions.authorizations) > 1:
                print(f"📱 检测到 {len(sessions.authorizations)} 个活跃会话，开始重置...")
                
                # 重置所有授权（踢掉其他设备）
                await client(ResetAuthorizationsRequest())
                
                # 等待一下，确保操作完成
                await asyncio.sleep(2)
                
                # 再次检查，确保只剩当前这一个会话
                sessions = await client(GetAuthorizationsRequest())
                remaining = len(sessions.authorizations)
                
                if remaining <= 1:
                    print(f"✅ 会话重置成功，当前仅剩 {remaining} 个会话")
                    return True
                else:
                    print(f"⚠️ 会话重置后仍有 {remaining} 个会话")
                    return False
            else:
                print("✅ 当前仅有1个会话，无需重置")
                return True
                
        except Exception as e:
            print(f"❌ 会话重置错误: {e}")
            return False
    
    async def get_verification_code_from_telegram(
        self, 
        client: TelegramClient, 
        timeout: int = 60
    ) -> Optional[str]:
        """
        从Telegram官方（777000）获取最新的验证码
        
        Args:
            client: 已登录的TelegramClient实例
            timeout: 超时时间（秒）
            
        Returns:
            str: 验证码，或None（如果未找到）
        """
        try:
            # 777000 是 Telegram 官方验证码账号
            entity = await client.get_entity(777000)
            
            # 获取最新消息
            messages = await client.get_messages(entity, limit=1)
            
            if not messages:
                print("⚠️ 未找到来自777000的消息")
                return None
            
            message_text = messages[0].message
            print(f"📨 收到消息: {message_text[:50]}...")
            
            # 从消息中提取验证码（5-6位数字）
            # 使用更精确的模式，通常验证码前后有特定的文本
            code_match = re.search(r"(?:code|код|验证码)[:\s]*(\d{5,6})|(\d{5,6})[.\s]*(?:is your|является вашим|是您的)", message_text, re.IGNORECASE)
            if not code_match:
                # 回退到简单匹配
                code_match = re.search(r"\b(\d{5,6})\b", message_text)
            
            if code_match:
                # 获取第一个非None的组
                code = code_match.group(1) or code_match.group(2)
                print(f"✅ 提取到验证码: {code}")
                return code
            else:
                print("⚠️ 未能从消息中提取验证码")
                return None
                
        except Exception as e:
            print(f"❌ 获取验证码失败: {e}")
            return None
    
    async def create_client_with_proxy(
        self,
        session_path: str,
        device: Optional[Dict] = None,
        lang_code: str = "en",
        system_lang_code: str = "en-US",
        tz: str = "UTC",
        proxy: Optional[Dict] = None
    ) -> TelegramClient:
        """
        创建配置好的TelegramClient实例
        
        Args:
            session_path: Session文件路径（不含.session扩展名）
            device: 设备信息字典
            lang_code: 语言代码
            system_lang_code: 系统语言代码
            tz: 时区
            proxy: 代理配置
            
        Returns:
            TelegramClient: 配置好的客户端实例
        """
        # 移除.session扩展名（如果存在）
        if session_path.endswith('.session'):
            session_path = session_path[:-8]
        
        # 创建客户端
        client = TelegramClient(
            session_path,
            self.api_id,
            self.api_hash,
            device_model=device.get('device_model', 'Desktop') if device else 'Desktop',
            system_version=device.get('system_version', 'Windows 10') if device else 'Windows 10',
            app_version=device.get('app_version', '4.8.0') if device else '4.8.0',
            lang_code=lang_code,
            system_lang_code=system_lang_code,
            proxy=proxy
        )
        
        return client
    
    async def recreate_session(
        self,
        old_session_path: str,
        new_session_path: str,
        phone_number: str,
        two_fa_password: Optional[str] = None,
        json_config_path: Optional[str] = None,
        output_folder: Optional[str] = None,
        device: Optional[Dict] = None,
        proxy: Optional[Dict] = None,
        convert_to_tdata: bool = False
    ) -> Tuple[bool, str]:
        """
        重新创建Session（完整流程）
        
        Args:
            old_session_path: 旧session文件路径
            new_session_path: 新session文件保存路径
            phone_number: 手机号（带国家代码）
            two_fa_password: 2FA密码（如果启用）
            json_config_path: JSON配置文件路径（可选）
            output_folder: 输出文件夹（可选）
            device: 设备信息
            proxy: 代理配置
            convert_to_tdata: 是否转换为TData格式
            
        Returns:
            Tuple[bool, str]: (成功与否, 消息)
        """
        old_client = None
        new_client = None
        
        try:
            print("=" * 60)
            print(f"🔄 开始重新授权流程")
            print(f"📱 手机号: {phone_number}")
            print(f"📂 旧Session: {old_session_path}")
            print(f"📂 新Session: {new_session_path}")
            print("=" * 60)
            
            # 移除.session扩展名
            old_session_base = old_session_path.replace('.session', '') if old_session_path.endswith('.session') else old_session_path
            new_session_base = new_session_path.replace('.session', '') if new_session_path.endswith('.session') else new_session_path
            
            # 步骤1: 连接旧客户端
            print("\n📡 步骤1: 连接旧Session...")
            old_client = TelegramClient(old_session_base, self.api_id, self.api_hash, proxy=proxy)
            await old_client.connect()
            
            if not await old_client.is_user_authorized():
                return False, "旧Session未授权或已失效"
            
            print("✅ 旧Session连接成功")
            
            # 步骤2: 重置所有会话
            print("\n🔄 步骤2: 重置所有会话...")
            reset_success = await self.reset_sessions(old_client)
            if not reset_success:
                print("⚠️ 会话重置失败，但继续执行...")
            
            # 步骤3: 创建新客户端
            print("\n🆕 步骤3: 创建新客户端...")
            new_client = await self.create_client_with_proxy(
                new_session_base,
                device=device,
                proxy=proxy
            )
            await new_client.connect()
            print("✅ 新客户端创建成功")
            
            # 步骤4: 请求验证码
            print("\n📲 步骤4: 请求验证码...")
            sent_code = await new_client(SendCodeRequest(
                phone_number,
                self.api_id,
                self.api_hash,
                CodeSettings()
            ))
            print(f"✅ 验证码已发送，phone_code_hash: {sent_code.phone_code_hash[:20]}...")
            
            # 等待验证码到达
            print(f"\n⏳ 等待验证码到达（{CODE_ARRIVAL_WAIT}秒）...")
            await asyncio.sleep(CODE_ARRIVAL_WAIT)  # 等待验证码到达
            
            # 步骤5: 从旧Session获取验证码
            print("\n📥 步骤5: 从旧Session获取验证码...")
            code = await self.get_verification_code_from_telegram(old_client)
            
            if not code:
                return False, "无法获取验证码，请检查旧Session是否能接收消息"
            
            print(f"✅ 成功获取验证码: {code}")
            
            # 步骤6: 新客户端登录
            print("\n🔐 步骤6: 使用验证码登录新Session...")
            try:
                await new_client.sign_in(
                    phone=phone_number,
                    phone_code_hash=sent_code.phone_code_hash,
                    code=code
                )
                print("✅ 登录成功（无需2FA）")
            except SessionPasswordNeededError:
                print("🔑 需要2FA密码...")
                if not two_fa_password:
                    return False, "账号需要2FA密码，但未提供"
                
                await new_client.sign_in(phone=phone_number, password=two_fa_password)
                print("✅ 使用2FA密码登录成功")
            
            # 验证新Session是否已授权
            if not await new_client.is_user_authorized():
                return False, "新Session登录失败"
            
            # 获取用户信息
            me = await new_client.get_me()
            user_info = f"ID:{me.id}"
            if me.username:
                user_info += f" @{me.username}"
            if me.first_name:
                user_info += f" {me.first_name}"
            
            print(f"✅ 新Session已授权: {user_info}")
            
            # 步骤7: 登出旧Session
            print("\n👋 步骤7: 登出旧Session...")
            try:
                await old_client.log_out()
                print("✅ 旧Session已登出")
            except Exception as e:
                print(f"⚠️ 登出旧Session时出错: {e}")
            
            # 步骤8: 断开连接
            print("\n🔌 步骤8: 断开所有连接...")
            await new_client.disconnect()
            if old_client:
                await old_client.disconnect()
            print("✅ 所有连接已断开")
            
            # 步骤9: 更新JSON配置（如果提供）
            if json_config_path and os.path.exists(json_config_path):
                print(f"\n📝 步骤9: 更新JSON配置...")
                try:
                    with open(json_config_path, "r+", encoding="utf-8") as f:
                        data = json.load(f)
                        data["twoFA"] = two_fa_password or ""
                        data["app_id"] = self.api_id
                        data["app_hash"] = self.api_hash
                        data["phone"] = phone_number
                        data["updated_at"] = datetime.now().isoformat()
                        
                        f.seek(0)
                        json.dump(data, f, indent=4, ensure_ascii=False)
                        f.truncate()
                    print("✅ JSON配置已更新")
                except Exception as e:
                    print(f"⚠️ 更新JSON配置失败: {e}")
            
            # 步骤10: 移动文件到输出目录（如果提供）
            if output_folder:
                print(f"\n📦 步骤10: 移动文件到输出目录...")
                try:
                    os.makedirs(output_folder, exist_ok=True)
                    
                    # 移动session文件
                    session_file = f"{new_session_base}.session"
                    if os.path.exists(session_file):
                        dest_session = os.path.join(output_folder, os.path.basename(session_file))
                        shutil.move(session_file, dest_session)
                        print(f"✅ Session文件已移动: {dest_session}")
                    
                    # 移动journal文件（如果存在）
                    journal_file = f"{new_session_base}.session-journal"
                    if os.path.exists(journal_file):
                        dest_journal = os.path.join(output_folder, os.path.basename(journal_file))
                        shutil.move(journal_file, dest_journal)
                    
                    # 移动JSON文件（如果存在）
                    if json_config_path and os.path.exists(json_config_path):
                        dest_json = os.path.join(output_folder, os.path.basename(json_config_path))
                        shutil.move(json_config_path, dest_json)
                        print(f"✅ JSON文件已移动: {dest_json}")
                    
                except Exception as e:
                    print(f"⚠️ 移动文件失败: {e}")
            
            # 步骤11: 转换为TData格式（如果需要且支持）
            if convert_to_tdata and OPENTELE_AVAILABLE:
                print(f"\n🔄 步骤11: 转换为TData格式...")
                try:
                    # 重新连接新Session以进行转换（使用相同的代理配置）
                    temp_client = TelegramClient(new_session_base, self.api_id, self.api_hash, proxy=proxy)
                    await temp_client.connect()
                    
                    if await temp_client.is_user_authorized():
                        # 使用opentele转换
                        tdesk = await temp_client.ToTDesktop(flag=UseCurrentSession)
                        
                        # 保存TData
                        tdata_folder = output_folder or os.path.dirname(new_session_base)
                        tdata_path = os.path.join(tdata_folder, "tdata")
                        tdesk.SaveTData(tdata_path)
                        print(f"✅ TData格式已保存: {tdata_path}")
                    
                    await temp_client.disconnect()
                    
                except Exception as e:
                    print(f"⚠️ TData转换失败: {e}")
            
            print("\n" + "=" * 60)
            print("🎉 重新授权完成！")
            print("=" * 60)
            
            return True, f"重新授权成功！用户: {user_info}"
            
        except Exception as e:
            error_msg = f"重新授权失败: {str(e)}"
            print(f"\n❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
            
        finally:
            # 确保所有连接都关闭
            try:
                if new_client and new_client.is_connected():
                    await new_client.disconnect()
            except:
                pass
            
            try:
                if old_client and old_client.is_connected():
                    await old_client.disconnect()
            except:
                pass


def get_device_info() -> Dict[str, str]:
    """
    获取设备信息
    
    Returns:
        Dict: 设备信息字典
    """
    return {
        'device_model': 'Desktop',
        'system_version': 'Windows 10',
        'app_version': '4.8.0',
        'lang_code': 'en',
        'system_lang_code': 'en-US'
    }


# 使用示例
async def example_usage():
    """使用示例"""
    # 配置
    api_id = 12345678  # 替换为你的API ID
    api_hash = "your_api_hash"  # 替换为你的API Hash
    
    # 创建管理器
    manager = ReauthorizationManager(api_id, api_hash)
    
    # 重新授权
    success, message = await manager.recreate_session(
        old_session_path="./sessions/old_session.session",
        new_session_path="./sessions/new_session.session",
        phone_number="+1234567890",
        two_fa_password="your_2fa_password",  # 如果有2FA
        json_config_path="./sessions/config.json",
        output_folder="./sessions/output",
        device=get_device_info(),
        proxy=None,  # 或者提供代理配置
        convert_to_tdata=True
    )
    
    print(f"\n结果: {message}")
    return success


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())
