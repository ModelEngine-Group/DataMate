"""
文档解析器基类

定义文档解析器的抽象接口
使用策略模式支持多种文档格式
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from langchain_core.documents import Document


class ParsedDocument:
    """解析后的文档

    包含文档的文本内容和元数据
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

    多页/多段结果合并为一个文档，用于 pipeline。

    Args:
        documents: LangChain 加载器返回的 Document 列表
        file_path: 源文件路径
        file_name: 文件名，若提供则优先使用
        **extra_metadata: 额外的元数据字段（会合并到返回的 metadata 中）

    Returns:
        ParsedDocument: 合并后的领域文档对象
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
        # 添加路径信息
        "absolute_directory_path": str(path.parent),
        "file_path": str(path),
    }

    # 合并额外的元数据
    meta.update(extra_metadata)

    # 合并第一个文档的元数据
    if documents and isinstance(documents[0].metadata, dict):
        first_meta = documents[0].metadata
        for k, v in first_meta.items():
            if k not in meta and v is not None:
                meta[k] = v

    return ParsedDocument(text=merged_text, metadata=meta, file_name=name)


class DocumentParser(ABC):
    """文档解析器基类（抽象类）

    对应 Java 的文档解析接口

    所有具体的解析器都需要继承此类并实现 parse 方法
    """

    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """解析文档

        Args:
            file_path: 文件路径（绝对路径）

        Returns:
            ParsedDocument: 解析后的文档对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或解析失败
        """
        pass

    def _get_file_name(self, file_path: str) -> str:
        """从文件路径中提取文件名

        Args:
            file_path: 文件路径

        Returns:
            文件名
        """
        return Path(file_path).name

    def _get_file_extension(self, file_path: str) -> str:
        """从文件路径中提取文件扩展名

        Args:
            file_path: 文件路径

        Returns:
            文件扩展名（包含点号，如 ".pdf"）
        """
        return Path(file_path).suffix.lower()

    def _build_metadata(
        self,
        file_path: str,
        **extra_fields
    ) -> Dict[str, Any]:
        """构建文档元数据

        Args:
            file_path: 文件路径
            **extra_fields: 额外的元数据字段

        Returns:
            元数据字典
        """
        path = Path(file_path)
        metadata = {
            "file_name": path.name,
            "file_extension": self._get_file_extension(file_path),
            "file_size": path.stat().st_size if path.exists() else 0,
        }
        metadata.update(extra_fields)
        return metadata
