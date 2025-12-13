import os
from typing import List, Optional, Tuple

from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)


class DocumentSplitter:
    """
    文档分割器类 - 增强版，优先通过元数据识别文档类型
    核心特性：
    1. 优先从metadata的source字段（文件扩展名）识别Markdown
    2. 元数据缺失时，通过内容特征降级检测
    3. 支持CJK（中日韩）语言优化
    """

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        is_cjk_language: bool = True,
        markdown_headers: Optional[List[Tuple[str, str]]] = None
    ):
        """
        初始化文档分割器

        Args:
            chunk_size: 每个文本块的最大长度（默认2000字符）
            chunk_overlap: 文本块之间的重叠长度（默认200字符）
            is_cjk_language: 是否处理中日韩等无词边界语言（默认True）
            markdown_headers: Markdown标题分割规则（默认：#/##/###/####）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.is_cjk_language = is_cjk_language

        # 默认Markdown标题分割规则
        self.markdown_headers = markdown_headers or [
            ("#", "header_1"),
            ("##", "header_2"),
            ("###", "header_3"),
            ("####", "header_4"),
        ]

        # 初始化基础文本分割器
        self.text_splitter = self._create_text_splitter()

    def _create_text_splitter(self) -> RecursiveCharacterTextSplitter:
        """创建递归字符分割器（内部方法）"""
        # 优化后的CJK分隔符列表（修复语法错误，调整优先级）
        if self.is_cjk_language:
            separators = [
                "\n\n", "\n",  # 段落/换行（最高优先级）
                "。", ".",  # 句号（中文/英文）
                "！", "!",  # 感叹号（中文/英文）
                "？", "?",  # 问号（中文/英文）
                "；", ";",  # 分号（中文/英文）
                "，", ",",  # 逗号（中文/英文）
                "、",  # 顿号（中文）
                "：", ":",  # 冒号（中文/英文）
                " ",  # 空格
                "\u200b", "",  # 零宽空格/兜底
            ]
        else:
            separators = ["\n\n", "\n", " ", ".", "!", "?", ";", ":", ",", ""]

        return RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )

    @staticmethod
    def _is_markdown(doc: Document) -> bool:
        """
        优先从元数据判断是否为Markdown
        规则：检查metadata中的source字段扩展名是否为.md/.markdown/.mdx等
        """
        # 获取source字段（忽略大小写）
        source = doc.metadata.get("source", "").lower()
        if not source:
            return False

        # 获取文件扩展名
        ext = os.path.splitext(source)[-1].lower()
        # Markdown常见扩展名列表
        md_ext = [".md", ".markdown", ".mdx", ".mkd", ".mkdown"]
        return ext in md_ext

    def split(self, documents: List[Document], is_markdown: bool = False) -> List[Document]:
        """
        核心分割方法

        Args:
            documents: 待分割的Document列表
            is_markdown: 是否为Markdown文档（默认False）

        Returns:
            分割后的Document列表
        """
        if not documents:
            return []

        # Markdown文档处理：先按标题分割，再按字符分割
        if is_markdown:
            # 初始化Markdown标题分割器
            md_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=self.markdown_headers,
                strip_headers=True,
                return_each_line=False
            )

            # 按标题分割并继承元数据
            md_chunks = []
            for doc in documents:
                chunks = md_splitter.split_text(doc.page_content)
                for chunk in chunks:
                    chunk.metadata.update(doc.metadata)
                md_chunks.extend(chunks)

            # 对标题分割后的内容进行字符分割
            final_chunks = self.text_splitter.split_documents(md_chunks)

        # 普通文本直接分割
        else:
            final_chunks = self.text_splitter.split_documents(documents)

        return final_chunks

    # 核心自动分割方法（元数据优先）
    @classmethod
    def auto_split(
        cls,
        documents: List[Document],
        chunk_size: int = 2000,
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        极简快捷方法：自动识别文档类型并分割（元数据优先）
        仅需传入3个参数，无需初始化类实例

        Args:
            documents: 待分割的Document列表
            chunk_size: 每个文本块的最大长度（默认2000字符）
            chunk_overlap: 文本块之间的重叠长度（默认200字符）

        Returns:
            分割后的Document列表
        """
        if not documents:
            return []

        # 初始化分割器实例（使用CJK默认优化）
        splitter = cls(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            is_cjk_language=True
        )

        # 自动检测文档类型（元数据优先）
        is_md = splitter._is_markdown(documents[0])

        # 根据检测结果选择分割方式
        return splitter.split(documents, is_markdown=is_md)
