#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文硬编码扫描工具
扫描用户可见路径中的中文硬编码，用于 i18n 迁移验证
"""

import re
import sys
import os

# 目标函数和模式 - 用户可见文本的输出位置
TARGET_FUNCS = (
    'reply_text',
    'edit_message_text',
    'safe_edit_message',
    'safe_send_message',
    'send_message',
    'InlineKeyboardButton(',
    'web.Response(',
    'query.answer(',
    'update.message.reply_text',
    'context.bot.send_message'
)

# 中文字符正则
CN = re.compile(r'[\u4e00-\u9fff]')

# 排除目录
EXCLUDE_DIRS = {'venv', '.git', 'node_modules', '__pycache__', '.pytest_cache', 'build', 'dist'}

# 排除文件（资源文件本身包含中文是正常的）
EXCLUDE_FILES = {'i18n_zh.json', 'zh.json', 'i18n_scan.py', 'README.md', 'README_CN.md'}

def should_check(path):
    """判断文件是否需要检查"""
    # 排除目录
    if any(part in EXCLUDE_DIRS for part in path.replace('\\', '/').split('/')):
        return False
    
    # 排除文件
    if os.path.basename(path) in EXCLUDE_FILES:
        return False
    
    # 只检查代码文件
    return path.endswith(('.py', '.html', '.txt', '.json')) and not path.endswith('_zh.json')

def scan(path):
    """扫描单个文件中的中文硬编码"""
    found = False
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                # 跳过注释行（Python #）
                stripped = line.strip()
                if stripped.startswith('#'):
                    continue
                
                # 跳过 print 语句（调试输出）
                if 'print(' in line or 'logger.' in line:
                    continue
                
                # 移除行内注释以避免误报
                code_part = line.split('#')[0]
                
                # 检查是否包含目标函数调用且包含中文
                if any(t in code_part for t in TARGET_FUNCS) and CN.search(code_part):
                    print(f"{path}:{i}: {line.strip()}")
                    found = True
    except Exception as e:
        print(f"⚠️ 无法扫描文件 {path}: {e}", file=sys.stderr)
    
    return found

def main():
    """主函数"""
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    
    print(f"🔍 扫描目录: {root}")
    print(f"🎯 目标函数: {', '.join(TARGET_FUNCS)}")
    print(f"📁 排除目录: {', '.join(EXCLUDE_DIRS)}")
    print(f"📄 排除文件: {', '.join(EXCLUDE_FILES)}")
    print("=" * 80)
    
    found_issues = False
    
    for dp, _, fns in os.walk(root):
        for fn in fns:
            p = os.path.join(dp, fn)
            if should_check(p):
                if scan(p):
                    found_issues = True
    
    print("=" * 80)
    if found_issues:
        print("❌ 发现中文硬编码！请迁移到 i18n 资源文件。")
        sys.exit(1)
    else:
        print("✅ 未发现中文硬编码。")
        sys.exit(0)

if __name__ == '__main__':
    main()
