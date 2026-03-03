"""
文档处理类型定义

包含 ParsedDocument（解析后文档）和 DocumentChunk（文档分块）。
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.documents import Document


@dataclass
class DocumentChunk:
    """文档分块

    包含分块的文本内容和元数据。

    Attributes:
        text: 分块文本内容
        metadata: 分块元数据（包含文件信息、分块索引等）
    """
    text: str
    metadata: dict

    def __repr__(self):
        return f"<DocumentChunk(text_length={len(self.text)}, metadata_keys={list(self.metadata.keys())})>"


class ParsedDocument:
    """解析后的文档

    包含文档的完整文本内容和元数据，由文档加载器生成，供分块器使用。

    Attributes:
        text: 文档完整文本内容
        metadata: 文档元数据（如文件名、扩展名、路径等）
        file_name: 文件名
    """

    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        file_name: str
    ):
        """初始化解析后的文档

        Args:
            text: 文档文本内容
            metadata: 文档元数据（如作者、创建时间等）
            file_name: 文件名
        """
        self.text = text
        self.metadata = metadata
        self.file_name = file_name

    def __repr__(self):
        return f"<ParsedDocument(file_name={self.file_name}, text_length={len(self.text)})>"


def langchain_documents_to_parsed(
    documents: List[Document],
    file_path: str,
    file_name: Optional[str] = None,
    **extra_metadata: Any,
) -> ParsedDocument:
    """将 LangChain Document 列表转换为 ParsedDocument

    多页/多段结果合并为一个文档，用于后续分块处理。

    Args:
        documents: LangChain 加载器返回的 Document 列表
        file_path: 源文件路径
        file_name: 文件名，若提供则优先使用
        **extra_metadata: 额外的元数据字段（会合并到返回的 metadata 中）

    Returns:
        ParsedDocument: 合并后的文档对象
    """
    path = Path(file_path)
    name = file_name or path.name

    if not documents:
        base_metadata = {
            "file_name": name,
            "file_extension": path.suffix.lower(),
            "file_size": path.stat().st_size if path.exists() else 0,
        }
        base_metadata.update(extra_metadata)
        return ParsedDocument(
            text="",
            metadata=base_metadata,
            file_name=name,
        )

    texts = [d.page_content for d in documents if d.page_content]
    merged_text = "\n\n".join(texts)

    meta: Dict[str, Any] = {
        "file_name": name,
        "file_extension": path.suffix.lower(),
        "file_size": path.stat().st_size if path.exists() else 0,
        "absolute_directory_path": str(path.parent),
        "file_path": str(path),
    }

    meta.update(extra_metadata)

    if documents and isinstance(documents[0].metadata, dict):
        first_meta = documents[0].metadata
        for k, v in first_meta.items():
            if k not in meta and v is not None:
                meta[k] = v

    return ParsedDocument(text=merged_text, metadata=meta, file_name=name)
