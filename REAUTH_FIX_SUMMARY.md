# 重新授权功能问题修复总结

## 修复日期
2025-12-10

## 问题描述

### 问题1：密码设置失败后JSON内容仍被更新
**现象**：当重新授权过程中设置新密码失败（例如遇到FloodError时），JSON文件和TData密码文件仍然被更新为新密码，导致后续登录失败。

**原因**：代码没有检查密码设置是否成功就直接更新了JSON和密码文件。

**日志示例**：
```
2025-12-10 06:19:06,704 - __main__ - INFO - 🔑 [213661910918.session] 步骤7: 设置新密码...
2025-12-10 06:19:07,376 - __main__ - WARNING - ⚠️ [213661910918.session] 设置新密码失败（Telegram错误）: FloodError
2025-12-10 06:19:07,376 - __main__ - INFO - ℹ️ [213661910918.session] 注意
```

### 问题2：打包方式不正确
**现象**：TData格式的打包结构不符合预期。

**错误的打包方式**：
```
文件类/ (直接展开了tdata内容)
├── key_datas
├── key_datas
├── D877F783D5D3EF8C
└── ...
```

**正确的打包方式**：
```
手机号/
├── tdata/
│   └── D877F783D5D3EF8C/
│       ├── key_datas
│       └── ...
└── 2fa.txt (如果密码设置成功)
```

## 修复方案

### 1. 密码更新控制机制

#### 1.1 添加密码设置状态跟踪
```python
# 在函数开始处初始化
password_set_success = False

# 步骤8: 设置新密码（如果提供）
if new_password and new_password != old_password:
    try:
        await new_client.edit_2fa(...)
        password_set_success = True  # 只有成功时设为True
    except Exception as e:
        # 密码设置失败，保持False
        pass
```

#### 1.2 条件更新JSON文件
```python
# 更新2FA密码（只在密码设置成功时更新）
if new_password and password_set_success:
    json_data['twoFA'] = new_password
    json_data['has_password'] = True
    logger.info(f"✅ [{file_name}] 已更新JSON文件中的twoFA字段")
elif new_password and not password_set_success:
    logger.info(f"ℹ️ [{file_name}] 密码设置失败，保持JSON文件中的旧密码")
```

#### 1.3 条件更新TData密码文件
```python
# 更新TData格式的密码文件（只在密码设置成功时更新）
if new_password and password_set_success and file_type == 'tdata' and original_tdata_path:
    # 创建或更新2fa.txt
    with open(password_file_path, 'w', encoding='utf-8') as f:
        f.write(new_password)
elif new_password and not password_set_success and file_type == 'tdata' and original_tdata_path:
    logger.info(f"ℹ️ [{file_name}] 密码设置失败，保持TData原始密码文件")
```

### 2. TData打包结构修正

#### 2.1 成功账号打包（修正后）
```python
if result_file_type == 'tdata':
    tdata_path = result.get('tdata_path')
    if tdata_path and os.path.exists(tdata_path):
        # 获取TData目录名（如D877F783D5D3EF8C）
        tdata_dirname = os.path.basename(tdata_path)
        
        # 添加TData目录下的所有文件，路径为：手机号/tdata/D877.../
        for root, dirs, files in os.walk(tdata_path):
            for file in files:
                file_full_path = os.path.join(root, file)
                rel_path_inside_tdata = os.path.relpath(file_full_path, tdata_path)
                arc_path = os.path.join(phone, 'tdata', tdata_dirname, rel_path_inside_tdata)
                zipf.write(file_full_path, arc_path)
        
        # 如果密码设置成功，创建2fa.txt文件
        password_set_success = result.get('password_set_success', False)
        new_password = result.get('new_password', '')
        if password_set_success and new_password and new_password != '无':
            password_content = new_password.encode('utf-8')
            password_arcname = os.path.join(phone, '2fa.txt')
            zipf.writestr(password_arcname, password_content)
```

#### 2.2 失败账号打包（保持原始结构）
```python
if os.path.isdir(file_path):
    # TData目录 - 打包为 手机号/tdata/D877...（完整保留原始结构）
    tdata_dirname = os.path.basename(file_path)
    for root, dirs, files in os.walk(file_path):
        for file in files:
            file_full_path = os.path.join(root, file)
            rel_path_inside_tdata = os.path.relpath(file_full_path, file_path)
            arc_path = os.path.join(phone, 'tdata', tdata_dirname, rel_path_inside_tdata)
            zipf.write(file_full_path, arc_path)
```

## 代码变更文件

- `tdata.py` - 重新授权功能的核心文件

## 测试验证

### 测试场景1：密码设置成功
- ✅ JSON文件中的twoFA字段正确更新
- ✅ TData目录中的2fa.txt文件正确创建/更新
- ✅ 打包后的zip文件包含`手机号/2fa.txt`

### 测试场景2：密码设置失败（FloodError等）
- ✅ JSON文件中的twoFA字段保持旧密码
- ✅ TData目录中的密码文件保持不变
- ✅ 日志中记录"密码设置失败，保持旧密码"

### 测试场景3：无密码或相同密码
- ✅ 不会出现未定义变量错误
- ✅ password_set_success正确初始化为False

### 测试场景4：TData打包结构
- ✅ 成功账号：`手机号/tdata/D877.../` 结构正确
- ✅ 失败账号：原始TData结构保持不变

## 质量保证

- ✅ Python语法检查通过
- ✅ CodeQL安全扫描通过（0个安全问题）
- ✅ 代码审查完成（2轮）
- ✅ 所有已知问题已修复

## 影响范围

- 重新授权功能（`/reauthorize`命令）
- TData格式账号的密码管理
- Session格式账号的密码管理
- 账号打包功能

## 向后兼容性

本次修复完全向后兼容，不会影响现有的账号和功能。

## 备注

1. 密码设置失败时，系统会保持原有密码，确保账号可以继续使用
2. 打包结构的修正使得TData格式的账号更易于管理和识别
3. 所有修复都添加了详细的日志，便于调试和问题追踪
