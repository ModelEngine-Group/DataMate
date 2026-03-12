"""
文件工具类

提供文件路径提取等通用工具方法。
"""
from pathlib import Path
from typing import Optional


def get_file_path(rag_file) -> Optional[str]:
    """获取 RAG 文件的绝对路径
    
    Args:
        rag_file: RAG 文件实体（需要有 file_metadata 属性）
        
    Returns:
        文件绝对路径，不存在返回 None
    """
    if not rag_file.file_metadata:
        return None
    
    file_path = rag_file.file_metadata.get("file_path")
    if file_path:
        return str(Path(file_path).absolute())
    return None
