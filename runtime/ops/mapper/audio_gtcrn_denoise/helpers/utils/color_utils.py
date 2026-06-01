#!/usr/bin/env python3
"""
命令行颜色工具
提供 ANSI 转义序列的颜色代码
"""

class Colors:
    """颜色代码"""
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # 样式
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # 重置
    RESET = '\033[0m'


def color_text(text: str, color: str, bold: bool = False) -> str:
    """给文本添加颜色
    
    Args:
        text: 要着色的文本
        color: 颜色代码
        bold: 是否加粗
        
    Returns:
        str: 带颜色代码的文本
    """
    if bold:
        return f"{Colors.BOLD}{color}{text}{Colors.RESET}"
    return f"{color}{text}{Colors.RESET}"


def info(msg: str) -> str:
    """INFO 级别消息（绿色）"""
    return f"{Colors.GREEN}[INFO]{Colors.RESET} {msg}"


def warning(msg: str) -> str:
    """WARNING 级别消息（黄色）"""
    return f"{Colors.YELLOW}[WARNING]{Colors.RESET} {msg}"


def error(msg: str) -> str:
    """ERROR 级别消息（红色）"""
    return f"{Colors.RED}[ERROR]{Colors.RESET} {msg}"


def ok(msg: str) -> str:
    """OK 级别消息（蓝色）"""
    return f"{Colors.BLUE}[OK]{Colors.RESET} {msg}"


def header(msg: str) -> str:
    """标题（蓝色加粗）"""
    return f"{Colors.BOLD}{Colors.BLUE}[PROCESS] {msg} {Colors.RESET}"


def success(msg: str) -> str:
    """成功消息（绿色加粗）"""
    return f"{Colors.BOLD}{Colors.GREEN}[SUCCESS] {msg} {Colors.RESET}"


def fail(msg: str) -> str:
    """失败消息（红色加粗）"""
    return f"{Colors.BOLD}{Colors.RED}[ERROR] {msg}{Colors.RESET}"


def question(msg: str) -> str:
    """问题消息（黄色）"""
    return f"{Colors.YELLOW}[WARNING] {msg}{Colors.RESET}"