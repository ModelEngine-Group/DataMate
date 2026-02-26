"""
RAG 模块 Schema 导出

集中导出所有数据模型、请求和响应 DTO
"""
from .enums import ProcessType
from app.db.models.knowledge_gen import RagType, FileStatus
from .types import RagChunk
from app.db.models.knowledge_gen import KnowledgeBase, RagFile
from .request import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseUpdateReq,
    KnowledgeBaseQueryReq,
    AddFilesReq,
    DeleteFilesReq,
    RagFileReq,
    RetrieveReq,
    FileInfo,
    PagingQuery,
    QueryRequest,
)
from .response import (
    ModelConfig,
    KnowledgeBaseResp,
    RagFileResp,
    RagChunkResp,
    SearchResult,
    PagedResponse,
)

__all__ = [
    # Enums
    "RagType",
    "ProcessType",
    "FileStatus",
    # Entities
    "KnowledgeBase",
    "RagFile",
    "RagChunk",
    # Requests
    "KnowledgeBaseCreateReq",
    "KnowledgeBaseUpdateReq",
    "KnowledgeBaseQueryReq",
    "AddFilesReq",
    "DeleteFilesReq",
    "RagFileReq",
    "RetrieveReq",
    "FileInfo",
    "PagingQuery",
    "QueryRequest",
    # Responses
    "ModelConfig",
    "KnowledgeBaseResp",
    "RagFileResp",
    "RagChunkResp",
    "SearchResult",
    "PagedResponse",
]
