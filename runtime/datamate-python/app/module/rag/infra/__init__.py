"""
RAG 基础设施层：文档加载、分片、管道

使用示例:
    from app.module.rag.infra import load_and_split, SplitOptions

    chunks = await load_and_split(
        "/path/to/doc.pdf",
        split_options=SplitOptions(
            process_type=ProcessType.PARAGRAPH_CHUNK,
            chunk_size=300,
        )
    )
"""
from app.module.rag.infra.pipeline import ingest_file_to_chunks, load_and_split
from app.module.rag.infra.options import SplitOptions, default_split_options

__all__ = [
    "load_and_split",
    "ingest_file_to_chunks",
    "SplitOptions",
    "default_split_options",
]
