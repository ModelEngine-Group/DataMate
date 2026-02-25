"""
RAG 文档加载与分片管道

使用全局 UniversalDocLoader 加载文档，分片后返回 DocumentChunk 列表。
"""
import asyncio
from typing import Any, List, Optional

from app.module.shared.common.document_loaders import UniversalDocLoader
from app.module.rag.infra.parser import langchain_documents_to_parsed
from app.module.rag.infra.splitter.base import DocumentChunk
from app.module.rag.infra.splitter.factory import DocumentSplitterFactory
from app.module.rag.schema.enums import ProcessType


async def load_and_split(
    file_path: str,
    split_options: Optional[dict] = None,
    **chunk_metadata: Any,
) -> List[DocumentChunk]:
    """加载文档并分块

    使用 UniversalDocLoader 加载文档，然后按指定策略分块。

    Args:
        file_path: 文件绝对路径
        split_options: 分片选项，None 表示使用默认（递归分块 500/50）
            - process_type: ProcessType 枚举，默认 DEFAULT_CHUNK
            - chunk_size: 块大小，默认 500
            - overlap_size: 重叠大小，默认 50
            - delimiter: 自定义分隔符
        **chunk_metadata: 写入每个 chunk.metadata 的额外字段

    Returns:
        List[DocumentChunk]: 分块列表
    """
    # 1. 加载文档（使用同步加载器并在异步上下文中运行）
    loader = UniversalDocLoader(file_path)
    documents = await asyncio.to_thread(loader.load)

    # 2. 准备 parser metadata
    parser_metadata = {}
    for key in ["original_file_id", "rag_file_id", "file_name"]:
        if key in chunk_metadata:
            parser_metadata[key] = chunk_metadata[key]

    # 3. 转换为 ParsedDocument（传递额外的 metadata）
    parsed = langchain_documents_to_parsed(documents, file_path, **parser_metadata)

    # 4. 获取分片选项
    options = split_options or {}
    process_type = options.get("process_type", ProcessType.DEFAULT_CHUNK)
    chunk_size = options.get("chunk_size", 500)
    overlap_size = options.get("overlap_size", 50)
    delimiter = options.get("delimiter")

    # 5. 合并 metadata 用于 chunk
    base_chunk_metadata = {
        "file_name": parsed.metadata.get("file_name", ""),
        "file_extension": parsed.metadata.get("file_extension", ""),
        "absolute_directory_path": parsed.metadata.get("absolute_directory_path", ""),
        "original_file_id": parsed.metadata.get("original_file_id", ""),
        "rag_file_id": parsed.metadata.get("rag_file_id", ""),
    }
    base_chunk_metadata.update(chunk_metadata)

    # 6. 分片
    splitter = DocumentSplitterFactory.create_splitter(
        process_type,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        delimiter=delimiter,
    )
    chunks = await splitter.split(
        parsed.text,
        file_name=parsed.file_name,
        **base_chunk_metadata,
    )

    return chunks


async def ingest_file_to_chunks(
    file_path: str,
    process_type: ProcessType = ProcessType.DEFAULT_CHUNK,
    chunk_size: int = 500,
    overlap_size: int = 50,
    delimiter: Optional[str] = None,
    **chunk_metadata: Any,
) -> List[DocumentChunk]:
    """从本地文件加载文档并分块（便捷入口）

    可被 ETL、URL 抓取、S3 等场景复用。

    Args:
        file_path: 文件绝对路径
        process_type: 分块策略
        chunk_size: 块大小
        overlap_size: 重叠大小
        delimiter: 自定义分隔符
        **chunk_metadata: 写入每个 chunk.metadata 的额外字段

    Returns:
        List[DocumentChunk]: 分块列表
    """
    split_options = {
        "process_type": process_type,
        "chunk_size": chunk_size,
        "overlap_size": overlap_size,
        "delimiter": delimiter,
    }
    return await load_and_split(
        file_path,
        split_options=split_options,
        **chunk_metadata,
    )
