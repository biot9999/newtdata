#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文硬编码扫描工具（改进版）
扫描用户可见路径中的中文硬编码，包括多行字符串，用于 i18n 迁移验证
"""

import re
import sys
import os
import ast

# 中文字符正则
CN = re.compile(r'[\u4e00-\u9fff]')

# 排除目录
EXCLUDE_DIRS = {'venv', '.git', 'node_modules', '__pycache__', '.pytest_cache', 'build', 'dist', 'locales'}

# 排除文件（资源文件本身包含中文是正常的）
EXCLUDE_FILES = {'i18n_zh.json', 'zh.json', 'i18n_scan.py', 'README.md', 'README_CN.md', 'en.json'}

def should_check(path):
    """判断文件是否需要检查"""
    # 排除目录
    if any(part in EXCLUDE_DIRS for part in path.replace('\\', '/').split('/')):
        return False
    
    # 排除文件
    if os.path.basename(path) in EXCLUDE_FILES:
        return False
    
    # 只检查代码文件
    return path.endswith(('.py',)) and not path.endswith('_zh.py')

def scan_multiline_strings(path):
    """扫描文件中包含中文的多行字符串"""
    found_issues = []
    
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
        
        # 方法1：检查多行字符串块（三引号）
        in_string = False
        string_start = 0
        string_lines = []
        
        for i, line in enumerate(lines, 1):
            # 检查是否有三引号
            if '"""' in line or "'''" in line:
                if not in_string:
                    # 开始多行字符串
                    in_string = True
                    string_start = i
                    string_lines = [line]
                else:
                    # 结束多行字符串
                    in_string = False
                    string_lines.append(line)
                    
                    # 检查这个字符串块是否包含中文
                    block_text = '\n'.join(string_lines)
                    if CN.search(block_text):
                        # 检查是否是用户可见的（不是注释，不是print/logger）
                        # 向前查找变量赋值或函数调用
                        context_start = max(0, string_start - 5)
                        context_end = min(len(lines), i + 5)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        # 跳过纯注释块
                        if not all(l.strip().startswith('#') for l in string_lines if l.strip()):
                            # 检查是否可能是用户可见的
                            is_user_visible = any(keyword in context for keyword in [
                                'text =', 'message =', 'reply_text', 'edit_message', 
                                'send_message', 'safe_edit', 'safe_send', 
                                'InlineKeyboardButton', 'web.Response'
                            ])
                            
                            # 排除明确的调试输出
                            is_debug = 'print(' in context or 'logger.' in context
                            
                            if is_user_visible and not is_debug:
                                found_issues.append({
                                    'line_start': string_start,
                                    'line_end': i,
                                    'preview': string_lines[0][:60] + '...' if len(string_lines[0]) > 60 else string_lines[0]
                                })
                    
                    string_lines = []
            elif in_string:
                string_lines.append(line)
        
        # 方法2：检查单行字符串中的中文（原有逻辑）
        for i, line in enumerate(lines, 1):
            # 跳过注释
            if line.strip().startswith('#'):
                continue
            
            # 跳过 print 和 logger
            if 'print(' in line or 'logger.' in line:
                continue
            
            code = line.split('#')[0]
            
            # 检查单行调用
            if any(keyword in code for keyword in [
                'reply_text', 'edit_message_text', 'safe_edit_message', 
                'safe_send_message', 'send_message', 'InlineKeyboardButton(',
                'query.answer(', 'web.Response('
            ]) and CN.search(code):
                found_issues.append({
                    'line_start': i,
                    'line_end': i,
                    'preview': line.strip()[:80]
                })
        
    except Exception as e:
        print(f"⚠️ 无法扫描文件 {path}: {e}", file=sys.stderr)
    
    return found_issues

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
