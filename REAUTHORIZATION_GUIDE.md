# 重新授权功能使用指南
# Re-authorization Feature Guide

## 概述 / Overview

重新授权功能允许用户完全自动化地重新创建Telegram Session文件，无需手动输入验证码。该功能特别适用于需要更换Session文件、被其他设备挤下线或需要统一2FA密码的场景。

The re-authorization feature allows users to automatically recreate Telegram Session files without manually entering verification codes. This is particularly useful for renewing session files, handling multi-device conflicts, or standardizing 2FA passwords.

## 核心功能 / Core Features

### 1. 会话重置 / Session Reset
- 自动踢掉所有其他设备的登录
- 确保只有当前会话有效
- 防止账号被多人同时使用

### 2. 自动验证码获取 / Automatic Code Retrieval
- 从Telegram官方账号（777000）自动读取验证码
- 无需人工输入
- 支持多语言验证码消息

### 3. 2FA支持 / 2FA Support
- 完整支持两步验证
- 可通过JSON配置提供2FA密码
- 支持手动输入2FA密码

### 4. 格式转换 / Format Conversion
- 可选TData格式转换
- 使用opentele库进行转换
- 同时保留Session格式

### 5. 无缝切换 / Seamless Transition
- 新Session成功登录后才登出旧Session
- 避免账号无法登录的风险
- 完整的错误处理机制

## 使用方法 / Usage

### 方法一：通过命令 / Via Command
```
/reauth
```

### 方法二：通过主菜单 / Via Main Menu
1. 点击主菜单中的"🔄 重新授权"按钮
2. 按照提示操作

## 操作流程 / Workflow

### 步骤1：准备文件 / Step 1: Prepare Files

准备包含以下文件的ZIP压缩包：
- Session文件（必需）: `phone.session`
- JSON配置文件（推荐）: `phone.json`

**JSON配置示例 / JSON Config Example:**
```json
{
  "phone": "+1234567890",
  "twoFA": "your_2fa_password",
  "app_id": 12345678,
  "app_hash": "your_api_hash"
}
```

### 步骤2：上传文件 / Step 2: Upload Files

1. 发送 `/reauth` 命令或点击"🔄 重新授权"
2. 点击"🚀 开始重新授权"
3. 上传准备好的ZIP文件

### 步骤3：确认信息 / Step 3: Confirm Information

系统会自动识别以下信息：
- 手机号码
- 2FA密码状态
- Session文件状态

如果需要修改，可以点击对应的编辑按钮。

### 步骤4：开始处理 / Step 4: Start Processing

1. 确认信息无误后，点击"🚀 开始处理"
2. 系统将自动完成以下操作：
   - 连接旧Session
   - 重置所有会话
   - 请求验证码
   - 自动获取验证码
   - 创建新Session
   - 登录新Session
   - 登出旧Session
   - 生成结果文件

### 步骤5：接收结果 / Step 5: Receive Results

处理完成后，您将收到一个包含以下内容的ZIP文件：
- 新的Session文件
- 更新的JSON配置
- TData格式文件（如果启用）

## 技术原理 / Technical Details

### 1. 会话重置 / Session Reset
```python
async def reset_sessions(client):
    sessions = await client(GetAuthorizationsRequest())
    if len(sessions.authorizations) > 1:
        await client(ResetAuthorizationsRequest())
```

使用Telegram的 `ResetAuthorizationsRequest` API重置所有授权。

### 2. 验证码获取 / Code Retrieval
```python
async def get_verification_code_from_telegram(client):
    entity = await client.get_entity(777000)
    messages = await client.get_messages(entity, limit=1)
    code_match = re.search(r"(?:code|код|验证码)[:\s]*(\d{5,6})", messages[0].message)
    return code_match.group(1) if code_match else None
```

从Telegram官方账号（777000）读取最新消息并提取验证码。

### 3. 新Session创建 / New Session Creation
```python
async def recreate_session(old_session_path, new_session_path, phone_number, two_fa_password):
    # 连接旧客户端
    old_client = TelegramClient(old_session_path, api_id, api_hash)
    await old_client.connect()
    
    # 创建新客户端并请求验证码
    new_client = TelegramClient(new_session_path, api_id, api_hash)
    await new_client.connect()
    sent_code = await new_client(SendCodeRequest(phone_number, api_id, api_hash, CodeSettings()))
    
    # 从旧客户端获取验证码
    code = await get_verification_code_from_telegram(old_client)
    
    # 使用验证码登录新客户端
    await new_client.sign_in(phone=phone_number, phone_code_hash=sent_code.phone_code_hash, code=code)
    
    # 处理2FA（如果有）
    try:
        await new_client.sign_in(phone=phone_number, password=two_fa_password)
    except SessionPasswordNeededError:
        pass
    
    # 登出旧客户端
    await old_client.log_out()
```

## 适用场景 / Use Cases

### 1. Session被其他人使用 / Session Used by Others
当您的Session文件被其他人使用，需要重新获取控制权时。

### 2. 多设备登录冲突 / Multi-device Conflicts
账号在多个设备上登录，需要清理并重新授权。

### 3. Session文件损坏 / Corrupted Session
Session文件损坏或无法使用，需要重新创建。

### 4. 统一2FA密码 / Standardize 2FA
需要将多个账号的2FA密码统一为相同的密码。

### 5. 更换设备环境 / Change Device/Environment
更换服务器或设备，需要迁移账号。

## 限制条件 / Limitations

### 必需条件 / Requirements
- ✅ 旧Session必须处于登录状态
- ✅ 账号必须能接收Telegram消息
- ✅ 需要有效的API ID和Hash
- ✅ 账号不能被Telegram限制

### 不支持场景 / Not Supported
- ❌ 账号被永久封禁
- ❌ 账号处于限制状态无法收消息
- ❌ Session文件完全失效
- ❌ 没有正确的2FA密码

## 安全建议 / Security Recommendations

### 1. 2FA密码安全 / 2FA Password Security
- **推荐**：使用JSON文件提供2FA密码
- **避免**：在消息中直接发送2FA密码
- **建议**：处理完成后及时更改2FA密码

### 2. Session文件安全 / Session File Security
- 妥善保管新生成的Session文件
- 不要与他人共享Session文件
- 定期更新Session文件

### 3. API凭证安全 / API Credentials Security
- 保护好API ID和Hash
- 不要在公开场合分享
- 如果泄露请及时重新生成

## 故障排除 / Troubleshooting

### 问题1：验证码获取失败 / Code Retrieval Failed
**可能原因 / Possible Causes:**
- 旧Session无法接收消息
- 网络连接问题
- Telegram服务延迟

**解决方案 / Solutions:**
- 确认旧Session处于登录状态
- 检查网络连接
- 等待几分钟后重试

### 问题2：2FA验证失败 / 2FA Verification Failed
**可能原因 / Possible Causes:**
- 2FA密码错误
- 账号没有启用2FA
- 密码包含特殊字符

**解决方案 / Solutions:**
- 确认2FA密码正确
- 确认账号是否真的启用了2FA
- 尝试重新输入密码

### 问题3：新Session登录失败 / New Session Login Failed
**可能原因 / Possible Causes:**
- 验证码已过期
- API ID/Hash不匹配
- 账号被限制

**解决方案 / Solutions:**
- 重新开始流程
- 检查API凭证
- 确认账号状态

### 问题4：代理连接问题 / Proxy Connection Issues
**可能原因 / Possible Causes:**
- 代理失效
- 代理配置错误
- 防火墙限制

**解决方案 / Solutions:**
- 测试代理可用性
- 更新代理配置
- 尝试使用其他代理

## 性能优化 / Performance Optimization

### 1. 批量处理 / Batch Processing
虽然当前版本支持单个账号处理，但可以通过以下方式优化批量场景：
- 使用脚本批量准备ZIP文件
- 按顺序依次处理
- 合理设置等待时间

### 2. 代理配置 / Proxy Configuration
- 使用稳定的代理服务
- 合理配置超时时间
- 启用快速模式

### 3. 错误恢复 / Error Recovery
- 保留旧Session备份
- 记录处理日志
- 准备回滚方案

## API参考 / API Reference

### ReauthorizationManager类 / ReauthorizationManager Class

#### 初始化 / Initialization
```python
manager = ReauthorizationManager(api_id, api_hash)
```

#### reset_sessions方法 / reset_sessions Method
```python
async def reset_sessions(client: TelegramClient) -> bool
```
重置所有会话，踢掉其他设备。

**参数 / Parameters:**
- `client`: 已登录的TelegramClient实例

**返回 / Returns:**
- `bool`: 成功返回True，失败返回False

#### recreate_session方法 / recreate_session Method
```python
async def recreate_session(
    old_session_path: str,
    new_session_path: str,
    phone_number: str,
    two_fa_password: Optional[str] = None,
    json_config_path: Optional[str] = None,
    output_folder: Optional[str] = None,
    device: Optional[Dict] = None,
    proxy: Optional[Dict] = None,
    convert_to_tdata: bool = False
) -> Tuple[bool, str]
```
重新创建Session文件。

**参数 / Parameters:**
- `old_session_path`: 旧session文件路径
- `new_session_path`: 新session文件保存路径
- `phone_number`: 手机号（带国家代码）
- `two_fa_password`: 2FA密码（可选）
- `json_config_path`: JSON配置文件路径（可选）
- `output_folder`: 输出文件夹（可选）
- `device`: 设备信息（可选）
- `proxy`: 代理配置（可选）
- `convert_to_tdata`: 是否转换为TData格式

**返回 / Returns:**
- `Tuple[bool, str]`: (成功与否, 消息)

## 开发者指南 / Developer Guide

### 扩展功能 / Extending Functionality

#### 添加自定义验证码提取 / Custom Code Extraction
```python
def custom_extract_code(message_text: str) -> Optional[str]:
    # 自定义正则表达式
    pattern = r"your_custom_pattern"
    match = re.search(pattern, message_text)
    return match.group(1) if match else None
```

#### 添加自定义设备信息 / Custom Device Info
```python
def custom_device_info() -> Dict[str, str]:
    return {
        'device_model': 'Custom Device',
        'system_version': 'Custom OS 1.0',
        'app_version': 'Custom App 1.0',
        'lang_code': 'zh',
        'system_lang_code': 'zh-CN'
    }
```

### 集成到其他项目 / Integration

```python
from reauthorization import ReauthorizationManager

# 初始化
manager = ReauthorizationManager(your_api_id, your_api_hash)

# 使用
success, message = await manager.recreate_session(
    old_session_path="./old.session",
    new_session_path="./new.session",
    phone_number="+1234567890",
    two_fa_password="your_password"
)

if success:
    print(f"成功: {message}")
else:
    print(f"失败: {message}")
```

## 更新日志 / Changelog

### v1.0.0 (2024)
- ✅ 首次发布
- ✅ 实现基础重新授权功能
- ✅ 支持自动验证码获取
- ✅ 支持2FA验证
- ✅ 支持TData格式转换
- ✅ 集成代理支持
- ✅ 完整的错误处理
- ✅ 安全性改进

## 常见问题 / FAQ

### Q1: 处理需要多长时间？
**A:** 通常需要30-60秒，取决于网络状况和Telegram服务器响应时间。

### Q2: 旧Session会被删除吗？
**A:** 旧Session会被登出，但文件不会被删除，建议您手动备份。

### Q3: 可以同时处理多个账号吗？
**A:** 当前版本需要逐个处理，批量功能计划在未来版本中添加。

### Q4: 支持哪些Session格式？
**A:** 支持Telethon的.session格式，可选转换为TData格式。

### Q5: 如果验证码一直获取不到怎么办？
**A:** 检查旧Session是否能正常接收777000的消息，或手动尝试在Telegram客户端登录查看验证码。

### Q6: 2FA密码会被保存吗？
**A:** 2FA密码会被保存在新的JSON配置文件中，请妥善保管。

### Q7: 支持代理吗？
**A:** 完全支持，会自动使用系统配置的代理。

### Q8: 失败后可以重试吗？
**A:** 可以，建议检查错误原因后重新开始流程。

## 技术支持 / Technical Support

如有问题或建议，请联系：
- Telegram: @PvBot
- GitHub Issues: [项目地址]

## 许可证 / License

本功能遵循项目主许可证。

---

**最后更新 / Last Updated:** 2024年
**版本 / Version:** 1.0.0
