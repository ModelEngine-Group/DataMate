"""
文本清理工具

提供文本清理和标准化的工具方法。
"""
import re
import logging
from typing import Optional


logger = logging.getLogger(__name__)


class TextCleaner:
    """文本清理工具类"""
    
    @staticmethod
    def clean(text: Optional[str]) -> str:
        """清理文本
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        text = TextCleaner._remove_control_characters(text)
        text = TextCleaner._normalize_whitespace(text)
        text = TextCleaner._remove_empty_lines(text)
        
        return text.strip()
    
    @staticmethod
    def _remove_control_characters(text: str) -> str:
        """移除控制字符"""
        control_chars = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]')
        return control_chars.sub('', text)
    
    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """标准化空白字符"""
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        return text
    
    @staticmethod
    def _remove_empty_lines(text: str) -> str:
        """移除空行"""
        lines = text.split('\n')
        return '\n'.join(line for line in lines if line.strip())
    
    @staticmethod
    def has_printable_content(text: str) -> bool:
        """检查是否包含可打印内容
        
        Args:
            text: 文本
            
        Returns:
            是否包含可打印内容
        """
        if not text:
            return False
        return any(c.isprintable() and not c.isspace() for c in text)
