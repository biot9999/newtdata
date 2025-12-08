# Telegram账号检测机器人 V8.0

一个功能强大的 Telegram 账号管理机器人，支持账号检测、格式转换、2FA管理、一键清理等功能。

## 主要功能

### 🚀 账号检测
- 批量检测 Telegram 账号状态
- SpamBot 限制检测
- 代理支持，提高检测速度
- 生成详细的检测报告

### 🔄 格式转换
- TData ↔ Session 格式互转
- 支持批量转换
- 保留账号所有信息

### 🔐 2FA 管理
- 批量修改 2FA 密码
- 忘记 2FA 密码恢复
- 批量添加 2FA 密码
- 安全可靠的密码管理

### 🧹 一键清理（新功能）

一键清理功能允许您快速清理 Telegram 账号的所有数据，包括群组、频道、聊天记录和联系人。

#### 功能特点

- **自动离开群组和频道**: 自动退出所有已加入的群组和频道
- **删除聊天记录**: 删除所有对话的聊天记录，支持双向撤回（需要权限）
- **清除联系人**: 移除所有联系人
- **归档对话**: 自动归档剩余的对话
- **详细报告**: 生成 CSV 和 JSON 格式的清理报告

#### 使用方法

1. **上传文件**
   - 在机器人主菜单中点击 "🧹 一键清理"
   - 上传包含 Session 或 TData 格式的 ZIP 文件

2. **确认操作**
   - 机器人会显示找到的账号数量和文件类型
   - **重要**: 仔细阅读警告信息
   - 点击 "✅ 确认清理" 开始清理

3. **等待完成**
   - 机器人会显示实时进度
   - 清理过程可能需要几分钟到几十分钟，取决于账号的对话数量
   - 请勿关闭机器人或重启程序

4. **查看报告**
   - 清理完成后，机器人会发送详细报告
   - 报告包含每个对话的清理状态和错误信息（如有）

#### ⚠️ 重要警告

- **不可逆操作**: 清理操作是不可逆的，删除的数据无法恢复
- **谨慎使用**: 请确保您真的需要清理账号数据
- **Telegram 限速**: 如果操作过快，Telegram 可能会临时限制您的操作，机器人会自动处理这种情况
- **权限限制**: 
  - 在您不是管理员的群组/频道中，只能删除自己的消息
  - 某些操作可能因权限不足而失败，这是正常的

#### 技术细节

**并发控制**:
- 离开群组/频道: 3 个并发
- 删除聊天记录: 2 个并发
- 删除联系人: 3 个并发
- 每个操作间隔: 0.3 秒 + 随机抖动
- 同一对话最小间隔: 1.5 秒

**错误处理**:
- 自动处理 FLOOD_WAIT 错误并重试
- 权限不足时优雅降级（仅删除自己的消息）
- 网络错误自动重试
- 所有错误都会记录在报告中

**安全保障**:
- 验证码记录（接码记录）不会被清理
- 账号登录状态保持不变
- 仅清理对话数据，不影响账号本身

#### 配置选项

可以通过 `.env` 文件调整以下参数：

```env
# 启用/禁用一键清理功能
ENABLE_ONE_CLICK_CLEANUP=true

# 并发设置
CLEANUP_LEAVE_CONCURRENCY=3
CLEANUP_DELETE_HISTORY_CONCURRENCY=2
CLEANUP_DELETE_CONTACTS_CONCURRENCY=3

# 延迟设置（秒）
CLEANUP_ACTION_SLEEP=0.3
CLEANUP_MIN_PEER_INTERVAL=1.5

# 是否默认撤回消息（双向删除）
CLEANUP_REVOKE_DEFAULT=true
```

#### 示例报告

清理完成后，您会收到两种格式的报告：

**CSV 报告** (用于 Excel/数据分析):
```csv
chat_id,title,type,actions_done,status,error,timestamp
-1001234567890,示例群组,group,"left, history_deleted",success,,2025-01-01T12:00:00
-1009876543210,示例频道,channel,"left, history_deleted",partial,Partial: only self messages deleted,2025-01-01T12:00:05
```

**JSON 报告** (用于程序处理):
```json
{
  "account_name": "account.session",
  "timestamp": "20250101_120000",
  "elapsed_time_seconds": 123.45,
  "statistics": {
    "groups_left": 15,
    "channels_left": 8,
    "histories_deleted": 50,
    "contacts_deleted": 100,
    "dialogs_closed": 45,
    "errors": 2,
    "skipped": 3
  },
  "actions": [...]
}
```

### 🔗 API 转换
- 生成 API 登录链接
- 实时接收验证码
- Web 界面查看验证码

### 📦 账号拆分
- 按国家/地区拆分账号
- 自动识别账号信息
- 智能分类归档

### 📝 文件管理
- 文件重命名
- 账户合并
- ZIP 文件处理

## 配置说明

### 环境变量

创建 `.env` 文件并配置以下参数：

```env
# 机器人配置
TOKEN=YOUR_BOT_TOKEN_HERE
API_ID=YOUR_API_ID_HERE
API_HASH=YOUR_API_HASH_HERE
ADMIN_IDS=123456789

# 会员配置
TRIAL_DURATION=30
TRIAL_DURATION_UNIT=minutes

# 性能配置
MAX_CONCURRENT_CHECKS=20
CHECK_TIMEOUT=15
SPAMBOT_WAIT_TIME=2.0

# 代理配置
USE_PROXY=true
PROXY_TIMEOUT=10
PROXY_FILE=proxy.txt
PROXY_CHECK_CONCURRENT=100
PROXY_CHECK_TIMEOUT=3
PROXY_AUTO_CLEANUP=true

# 一键清理配置
ENABLE_ONE_CLICK_CLEANUP=true
CLEANUP_LEAVE_CONCURRENCY=3
CLEANUP_DELETE_HISTORY_CONCURRENCY=2
CLEANUP_DELETE_CONTACTS_CONCURRENCY=3
CLEANUP_ACTION_SLEEP=0.3
CLEANUP_MIN_PEER_INTERVAL=1.5
CLEANUP_REVOKE_DEFAULT=true

# Web 服务配置
BASE_URL=http://127.0.0.1:5000
WEB_SERVER_PORT=8080
```

### 代理配置

在 `proxy.txt` 文件中配置代理：

```
# HTTP 代理
127.0.0.1:8080
127.0.0.1:8080:username:password

# SOCKS5 代理
socks5:127.0.0.1:1080:username:password

# 住宅代理
host.abcproxy.vip:4950:username:password
```

## 安装

1. **克隆仓库**
```bash
git clone https://github.com/biot9999/newtdata.git
cd newtdata
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
- 复制 `.env.example` 为 `.env`
- 填写必要的配置信息

4. **运行机器人**
```bash
python tdata.py
```

## 依赖库

- python-telegram-bot==13.15
- telethon>=1.34
- opentele>=1.15
- flask>=2.2
- aiohttp
- 更多详见 `requirements.txt`

## 目录结构

```
newtdata/
├── tdata.py                    # 主程序
├── account_classifier.py       # 账号分类器
├── login_api.py               # 登录 API 服务
├── apiclient.py               # API 客户端
├── services/                  # 服务模块
│   ├── __init__.py
│   └── one_click_cleaner.py   # 一键清理服务
├── sessions/                  # Session 文件目录
├── results/                   # 结果文件目录
│   └── cleanup_reports/       # 清理报告目录
├── uploads/                   # 上传文件目录
└── device_params/             # 设备参数目录
```

## 注意事项

### 安全提示

1. **保护您的凭据**: 不要泄露 Bot Token、API ID 和 API Hash
2. **会话文件安全**: Session 文件包含登录凭据，请妥善保管
3. **代理安全**: 使用可信的代理服务器

### 使用限制

1. **Telegram 限速**: 
   - 频繁操作可能触发 Telegram 的限速机制
   - 机器人会自动处理 FLOOD_WAIT 错误
   - 建议合理设置并发数量

2. **权限限制**:
   - 某些操作需要相应的权限
   - 在他人的群组/频道中可能无法执行某些操作

3. **文件大小限制**:
   - 上传文件限制为 100MB
   - 对于大量账号，建议分批处理

### 常见问题

**Q: 一键清理后可以恢复吗？**
A: 不可以。清理操作是不可逆的，请谨慎使用。

**Q: 为什么某些群组无法退出？**
A: 可能是因为权限限制或网络问题。检查报告中的错误信息。

**Q: 清理需要多长时间？**
A: 取决于账号的对话数量，通常几分钟到几十分钟不等。

**Q: 会删除哪些数据？**
A: 会删除群组、频道、聊天记录和联系人，但不会影响验证码记录和账号本身。

**Q: 遇到 FLOOD_WAIT 怎么办？**
A: 机器人会自动处理，等待指定时间后继续。请耐心等待。

## 更新日志

### V8.0 (2025-01-XX)
- ✨ 新增一键清理功能
- 🚀 提升账号检测速度
- 🔧 优化代理管理
- 📊 改进报告生成
- 🐛 修复已知问题

## 许可证

本项目仅供学习和研究使用。

## 联系方式

- Telegram: @PvBot
- Issues: https://github.com/biot9999/newtdata/issues

---

**免责声明**: 使用本工具需遵守 Telegram 服务条款。作者不对使用本工具造成的任何后果负责。
