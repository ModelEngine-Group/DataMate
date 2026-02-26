"""
文档加载器

封装 UniversalDocLoader，提供统一的文档加载接口。
"""
import asyncio
from typing import List

from langchain_core.documents import Document

from app.module.shared.common.document_loaders import UniversalDocLoader


async def load_document(file_path: str) -> List[Document]:
    """加载文档（异步封装）

    使用 UniversalDocLoader 加载文档，支持多种格式。

    Args:
        file_path: 文件绝对路径

    Returns:
        LangChain Document 列表
    """
    loader = UniversalDocLoader(file_path)
    return await asyncio.to_thread(loader.load)
