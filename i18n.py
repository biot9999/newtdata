#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言国际化支持 (i18n)
"""

import json
import os
from typing import Dict, Optional

class I18n:
    """多语言管理器"""
    
    def __init__(self, locales_dir: str = 'locales', default_lang: str = 'zh'):
        """
        初始化多语言管理器
        
        Args:
            locales_dir: 语言文件目录
            default_lang: 默认语言
        """
        self.locales_dir = locales_dir
        self.default_lang = default_lang
        self.translations: Dict[str, dict] = {}
        self.user_languages: Dict[int, str] = {}  # user_id -> language_code
        self.cache: Dict[str, str] = {}  # 翻译缓存
        
        # 加载所有语言文件
        self.load_languages()
    
    def load_languages(self):
        """加载所有语言文件"""
        if not os.path.exists(self.locales_dir):
            os.makedirs(self.locales_dir)
            print(f"📁 创建多语言目录: {self.locales_dir}")
            return
        
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]  # 移除 .json
                file_path = os.path.join(self.locales_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                    print(f"✅ 已加载语言: {lang_code} ({filename})")
                except Exception as e:
                    print(f"❌ 加载语言文件失败 {filename}: {e}")
        
        if not self.translations:
            print(f"⚠️ 未找到任何语言文件")
    
    def set_user_language(self, user_id: int, lang_code: str) -> bool:
        """设置用户语言"""
        if lang_code in self.translations:
            self.user_languages[user_id] = lang_code
            return True
        return False
    
    def get_user_language(self, user_id: int) -> str:
        """获取用户语言"""
        return self.user_languages.get(user_id, self.default_lang)
    
    def get(self, user_id: int, key: str, **kwargs) -> str:
        """
        获取翻译文本
        
        Args:
            user_id: 用户ID
            key: 翻译键，支持点号分隔，如 'start.welcome'
            **kwargs: 格式化参数
        
        Returns:
            翻译后的文本
        
        Examples:
            >>> i18n.get(123, 'start.welcome')
            '👋 欢迎使用 TData 机器人！'
            
            >>> i18n.get(123, 'check.processing', current=10, total=100)
            '⏳ 正在处理... 进度: 10/100'
        """
        lang = self.get_user_language(user_id)
        
        # 生成缓存键
        cache_key = f"{lang}:{key}"
        
        # 检查缓存（仅当没有参数时）
        if not kwargs and cache_key in self.cache:
            return self.cache[cache_key]
        
        # 尝试获取用户语言的翻译
        text = self._get_translation(lang, key)
        
        # 如果没找到，使用默认语言
        if text is None and lang != self.default_lang:
            text = self._get_translation(self.default_lang, key)
        
        # 还是没找到，返回键本身
        if text is None:
            print(f"⚠️ 翻译键不存在: {key} (语言: {lang})")
            return key
        
        # 格式化文本
        try:
            result = text.format(**kwargs) if kwargs else text
        except KeyError as e:
            print(f"⚠️ 翻译参数缺失: {key}, 缺少 {e}")
            result = text
        
        # 缓存结果（仅当没有参数时）
        if not kwargs:
            self.cache[cache_key] = result
        
        return result
    
    def _get_translation(self, lang: str, key: str) -> Optional[str]:
        """从指定语言获取翻译"""
        if lang not in self.translations:
            return None
        
        # 分割键（支持 'start.welcome' 格式）
        keys = key.split('.')
        data = self.translations[lang]
        
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return None
        
        return data if isinstance(data, str) else None
    
    def get_available_languages(self) -> Dict[str, str]:
        """获取可用语言列表"""
        # 从翻译文件中获取语言名称
        languages = {}
        for lang_code in self.translations:
            lang_name = self._get_translation(lang_code, 'language_name')
            if lang_name:
                languages[lang_code] = lang_name
            else:
                # 回退到默认名称
                default_names = {
                    'zh': '🇨🇳 简体中文',
                    'en': '🇺🇸 English',
                    'ru': '🇷🇺 Русский'
                }
                languages[lang_code] = default_names.get(lang_code, lang_code.upper())
        
        return languages
    
    def reload(self):
        """热重载翻译文件"""
        print("🔄 重新加载翻译文件...")
        self.translations.clear()
        self.cache.clear()
        self.load_languages()
        print("✅ 翻译文件重载完成")
