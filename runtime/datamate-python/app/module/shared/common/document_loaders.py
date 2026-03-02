from pathlib import Path
from typing import List, Union, Optional

from langchain_community.document_loaders import (
    TextLoader,
    JSONLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
    UnstructuredFileLoader,
    UnstructuredExcelLoader,
    PyPDFLoader,
    Docx2txtLoader, BSHTMLLoader
)
from langchain_core.documents import Document

from app.core.logging import get_logger

log = get_logger(__name__)

class UniversalDocLoader:
    """
    通用泛文本文档加载类
    支持格式：TXT/JSON/CSV/Markdown/Word(.docx)/PPT(.pptx)/PDF/Excel(.xlsx,.xls)/各种文本文件
    """
    # 格式-加载器映射（轻量优先）
    SUPPORTED_FORMATS = {
        # 纯文本类
        ".txt": TextLoader,
        ".json": JSONLoader,
        ".csv": CSVLoader,
        ".md": UnstructuredMarkdownLoader,
        ".markdown": UnstructuredMarkdownLoader,
        ".log": TextLoader,
        ".xml": TextLoader,
        ".html": BSHTMLLoader,
        ".htm": BSHTMLLoader,
        ".yaml": TextLoader,
        ".yml": TextLoader,
        # 办公文档类
        ".docx": Docx2txtLoader,
        ".doc": Docx2txtLoader,
        ".pptx": UnstructuredFileLoader,
        ".ppt": UnstructuredFileLoader,
        ".xlsx": UnstructuredExcelLoader,
        ".xls": UnstructuredExcelLoader,
        # PDF 类
        ".pdf": PyPDFLoader
    }

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path).resolve()
        self.file_suffix = self.file_path.suffix.lower()
        log.info(f"初始化文档加载器: {self.file_path} (格式: {self.file_suffix})")
        self._validate_file()

    def _validate_file(self) -> None:
        """验证文件存在性和格式支持性"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        if self.file_suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的格式: {self.file_suffix} | 支持格式: {list(self.SUPPORTED_FORMATS.keys())}"
            )

    def load(
        self,
        file_format: Optional[str] = None,
        **loader_kwargs
    ) -> List[Document]:
        """
        加载文档并返回 LangChain Document 列表
        :param file_format: 手动指定格式（如 ".pdf"），默认自动识别
        :param loader_kwargs: 传递给具体加载器的参数（如 JSONLoader 的 jq_schema）
        :return: List[Document]
        """
        # 确定目标格式
        target_format = file_format.lower() if file_format else self.file_suffix
        loader_cls = self.SUPPORTED_FORMATS[target_format]

        # 加载器默认参数优化
        loader_kwargs = self._set_default_kwargs(loader_cls, loader_kwargs)

        # 初始化并加载
        loader = loader_cls(str(self.file_path), **loader_kwargs)
        return loader.load()

    @staticmethod
    def _set_default_kwargs(loader_cls, kwargs: dict) -> dict:
        """为不同加载器设置默认参数，简化调用"""
        if loader_cls == JSONLoader and "jq_schema" not in kwargs:
            kwargs.setdefault("jq_schema", ".")
            kwargs.setdefault("text_content", False)
        if loader_cls == CSVLoader and "csv_args" not in kwargs:
            kwargs["csv_args"] = {"delimiter": ","}
        if loader_cls == UnstructuredExcelLoader:
            # Excel 文件使用 "single" 模式，避免生成过多无意义的元素
            # "elements" 模式会为每个单元格生成单独的文档，可能导致大量空内容
            if "mode" not in kwargs:
                kwargs.setdefault("mode", "single")
            # 确保加载表格结构
            kwargs.setdefault("include_header", True)
        if loader_cls == UnstructuredFileLoader and "mode" not in kwargs:
            kwargs.setdefault("mode", "elements")
        return kwargs


# 文档加载器便捷函数
def load_documents(
    file_path: Union[str, Path],
    file_format: Optional[str] = None,
    **loader_kwargs
) -> List[Document]:
    """快速加载文档的便捷函数"""
    loader = UniversalDocLoader(file_path)
    return loader.load(file_format=file_format, **loader_kwargs)
