#!/usr/bin/env python3
"""
命令行日志标签工具。

DataMate/Ray 日志会直接展示 stdout，ANSI 颜色控制符会污染页面日志，
因此这里保留原函数名但只输出纯文本标签。
"""

class Colors:
    """兼容旧调用的空颜色代码。"""
    BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
    BG_BLACK = BG_RED = BG_GREEN = BG_YELLOW = BG_BLUE = BG_MAGENTA = BG_CYAN = BG_WHITE = ""
    BOLD = UNDERLINE = BLINK = REVERSE = RESET = ""


def color_text(text: str, color: str, bold: bool = False) -> str:
    """给文本添加颜色
    
    Args:
        text: 要着色的文本
        color: 颜色代码
        bold: 是否加粗
        
    Returns:
        str: 带颜色代码的文本
    """
    return text


def info(msg: str) -> str:
    """INFO 级别消息"""
    return f"[INFO] {msg}"


def warning(msg: str) -> str:
    """WARNING 级别消息"""
    return f"[WARNING] {msg}"


def error(msg: str) -> str:
    """ERROR 级别消息"""
    return f"[ERROR] {msg}"


def ok(msg: str) -> str:
    """OK 级别消息"""
    return f"[OK] {msg}"


def header(msg: str) -> str:
    """标题"""
    return f"[PROCESS] {msg}"


def success(msg: str) -> str:
    """成功消息"""
    return f"[SUCCESS] {msg}"


def fail(msg: str) -> str:
    """失败消息"""
    return f"[ERROR] {msg}"


def question(msg: str) -> str:
    """问题消息"""
    return f"[WARNING] {msg}"
