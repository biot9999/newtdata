# 注册时间查询功能 (Registration Time Query Feature)

## 功能概述 (Overview)

本功能允许用户查询Telegram账号的注册时间，并按时间自动分类。由于Telegram官方API不直接提供准确的注册日期，我们使用用户ID范围来估算注册时期。

This feature allows users to query the registration time of Telegram accounts and automatically classify them by time period. Since Telegram's official API does not directly provide accurate registration dates, we estimate the registration period based on user ID ranges.

## 功能特点 (Features)

### 1. 注册时间估算 (Registration Time Estimation)
- 基于用户ID范围估算注册年份
- 涵盖2013年至今的用户
- 准确度：年份级别

### 2. 自动分类 (Automatic Classification)
- 按注册年份分类
- 按时期范围分类（如"Early Adopters", "2020 Wave"等）
- 自动生成分类报告

### 3. 批量处理 (Batch Processing)
- 支持批量查询多个账号
- 并发处理提高效率
- 实时进度显示

### 4. 文件格式支持 (File Format Support)
- Session格式 (.session)
- TData格式（自动转换）
- ZIP压缩包上传

## 使用方法 (Usage)

### 1. 启动查询 (Start Query)
在机器人主菜单中点击"📅 注册时间"按钮，或发送命令：
```
/registration
```

### 2. 上传文件 (Upload File)
上传包含账号的ZIP文件：
- Session文件 (.session)
- TData文件夹
- 混合格式

### 3. 等待处理 (Wait for Processing)
系统会自动：
- 解压文件
- 连接账号
- 查询用户信息
- 估算注册时间
- 生成分类

### 4. 接收结果 (Receive Results)
您将收到：
- 详细分析报告（TXT文件）
- 按年份分类的ZIP文件
- 统计信息

## 技术细节 (Technical Details)

### 用户ID范围 (User ID Ranges)

根据Telegram的用户ID分配历史，我们建立了以下估算范围：

| 用户ID范围 | 估算年份 | 描述 |
|-----------|---------|------|
| 0 - 10,000,000 | 2013 | Early Adopters |
| 10,000,000 - 50,000,000 | 2014 | 2014 Wave |
| 50,000,000 - 150,000,000 | 2015 | 2015 Wave |
| 150,000,000 - 300,000,000 | 2016 | 2016 Wave |
| 300,000,000 - 500,000,000 | 2017 | 2017 Wave |
| 500,000,000 - 800,000,000 | 2018 | 2018 Wave |
| 800,000,000 - 1,200,000,000 | 2019 | 2019 Wave |
| 1,200,000,000 - 1,700,000,000 | 2020 | 2020 Wave |
| 1,700,000,000 - 2,300,000,000 | 2021 | 2021 Wave |
| 2,300,000,000 - 3,000,000,000 | 2022 | 2022 Wave |
| 3,000,000,000 - 4,000,000,000 | 2023 | 2023 Wave |
| 4,000,000,000+ | 2024+ | Recent Users |

### API使用 (API Usage)

我们使用以下Telegram API：
- `GetFullUserRequest`: 获取用户完整信息
- `get_me()`: 获取自己的账号信息

提取的信息包括：
- 用户ID
- 用户名
- 手机号
- 共同群组数量
- 个人简介

### 错误处理 (Error Handling)

系统会处理以下情况：
- `UserPrivacyRestrictedError`: 隐私设置限制
- `FloodWaitError`: 请求过于频繁
- 未授权的Session
- 网络连接问题

## 输出文件 (Output Files)

### 1. 分析报告 (Analysis Report)
文件名：`registration_report_YYYYMMDD_HHMMSS.txt`

内容包括：
- 总体统计
- 按年份分类统计
- 按时期分类统计
- 详细账号信息列表

### 2. 分类ZIP文件 (Classified ZIP Files)
文件名：`registration_[年份]年_[数量]个_YYYYMMDD_HHMMSS.zip`

每个ZIP包含：
- 该年份注册的所有账号
- Session文件
- JSON配置文件（如果有）

## 注意事项 (Notes)

### 1. 准确度 (Accuracy)
- 注册时间是基于用户ID范围的**估算值**
- Telegram官方API不提供准确的注册日期
- 估算准确度为年份级别

### 2. 权限要求 (Permission Requirements)
- 需要会员权限
- 账号必须已授权
- 需要有效的API凭据

### 3. 性能考虑 (Performance Considerations)
- 批量查询有延迟（防止被限流）
- 建议一次处理不超过100个账号
- 每个账号查询间隔约1秒

### 4. 隐私保护 (Privacy Protection)
- 仅查询已授权账号
- 不存储敏感信息
- 临时文件自动清理

## 常见问题 (FAQ)

### Q1: 为什么注册时间不是精确日期？
A: Telegram官方API不提供准确的注册日期。我们使用用户ID范围来估算注册时期，这种方法只能精确到年份。

### Q2: 估算的准确度如何？
A: 对于年份级别的估算，准确度较高（约95%以上）。但具体到月份或日期则不准确。

### Q3: 可以查询其他用户的注册时间吗？
A: 可以，但需要对方没有设置隐私限制。如果对方设置了隐私保护，系统会返回"隐私设置限制"错误。

### Q4: 为什么有些账号显示"错误/未知"？
A: 可能的原因：
- Session未授权或已失效
- 账号被封禁或冻结
- 网络连接问题
- 隐私设置限制

### Q5: 支持哪些文件格式？
A: 支持Session格式和TData格式。TData格式会自动转换为Session进行查询。

## 技术支持 (Technical Support)

如有问题或建议，请联系开发团队。

## 更新日志 (Changelog)

### v1.0.0 (2025-12-10)
- ✨ 初始版本发布
- ✨ 支持Session和TData格式
- ✨ 按年份自动分类
- ✨ 生成详细分析报告
- ✨ 批量并发处理

## 许可证 (License)

本功能是Telegram账号检测机器人的一部分，遵循与主程序相同的许可证。

---

**注意**: 本功能仅供学习和研究使用，请遵守Telegram服务条款和相关法律法规。
**Note**: This feature is for learning and research purposes only. Please comply with Telegram's Terms of Service and relevant laws and regulations.
