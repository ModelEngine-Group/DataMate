"""
文档处理管道

提供统一的文档加载和分块入口，合并原有的 pipeline.py 和 options.py。
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.module.rag.infra.document.loader import load_document
from app.module.rag.infra.document.splitter import DocumentSplitterFactory
from app.module.rag.infra.document.types import (
    DocumentChunk,
    ParsedDocument,
    langchain_documents_to_parsed,
)
from app.module.rag.schema.enums import ProcessType


@dataclass
class SplitOptions:
    """文档分片选项

    Attributes:
        process_type: 分片策略
        chunk_size: 块大小（字符）
        overlap_size: 块间重叠
        delimiter: 仅 CUSTOM_SEPARATOR_CHUNK 时有效
    """
    process_type: ProcessType = ProcessType.DEFAULT_CHUNK
    chunk_size: int = 500
    overlap_size: int = 50
    delimiter: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "process_type": self.process_type,
            "chunk_size": self.chunk_size,
            "overlap_size": self.overlap_size,
            "delimiter": self.delimiter,
        }


def default_split_options() -> SplitOptions:
    """默认分片选项：递归分块 500/50"""
    return SplitOptions()


async def load_and_split(
    file_path: str,
    split_options: Optional[SplitOptions] = None,
    **chunk_metadata: Any,
) -> List[DocumentChunk]:
    """加载文档并分块

    使用 UniversalDocLoader 加载文档，然后按指定策略分块。

    Args:
        file_path: 文件绝对路径
        split_options: 分片选项，None 表示使用默认
        **chunk_metadata: 写入每个 chunk.metadata 的额外字段

    Returns:
        分块列表
    """
    documents = await load_document(file_path)

    parser_metadata = {}
    for key in ["original_file_id", "rag_file_id", "file_name"]:
        if key in chunk_metadata:
            parser_metadata[key] = chunk_metadata[key]

    parsed = langchain_documents_to_parsed(documents, file_path, **parser_metadata)

    options = split_options or default_split_options()

    base_chunk_metadata = {
        "file_name": parsed.metadata.get("file_name", ""),
        "file_extension": parsed.metadata.get("file_extension", ""),
        "absolute_directory_path": parsed.metadata.get("absolute_directory_path", ""),
        "original_file_id": parsed.metadata.get("original_file_id", ""),
        "rag_file_id": parsed.metadata.get("rag_file_id", ""),
    }
    base_chunk_metadata.update(chunk_metadata)

    splitter = DocumentSplitterFactory.create_splitter(
        options.process_type,
        chunk_size=options.chunk_size,
        overlap_size=options.overlap_size,
        delimiter=options.delimiter,
    )

    return await splitter.split(parsed.text, **base_chunk_metadata)


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
        分块列表
    """
    split_options = SplitOptions(
        process_type=process_type,
        chunk_size=chunk_size,
        overlap_size=overlap_size,
        delimiter=delimiter,
    )
    return await load_and_split(file_path, split_options=split_options, **chunk_metadata)
