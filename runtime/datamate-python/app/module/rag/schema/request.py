"""
RAG 模块请求 DTO

使用 Pydantic 定义所有请求参数验证
与 Java DTO 保持字段一致和验证规则一致
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from .enums import ProcessType
from app.db.models.knowledge_gen import RagType, FileStatus


class KnowledgeBaseCreateReq(BaseModel):
    """知识库创建请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseCreateReq
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        description="知识库名称（必须以字母开头，只能包含字母、数字和下划线）"
    )
    description: Optional[str] = Field(
        None,
        max_length=512,
        description="知识库描述"
    )
    type: RagType = Field(
        default=RagType.DOCUMENT,
        description="RAG 类型"
    )
    embedding_model: str = Field(
        ...,
        min_length=1,
        alias="embeddingModel",
        description="嵌入模型ID"
    )
    chat_model: Optional[str] = Field(
        None,
        alias="chatModel",
        description="聊天模型ID"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "my_knowledge_base",
                "description": "我的知识库",
                "type": "DOCUMENT",
                "embeddingModel": "text-embedding-ada-002",
                "chatModel": "gpt-4"
            }
        }


class KnowledgeBaseUpdateReq(BaseModel):
    """知识库更新请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseUpdateReq
    """
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$",
        description="知识库名称"
    )
    description: Optional[str] = Field(
        None,
        max_length=512,
        description="知识库描述"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "updated_knowledge_base",
                "description": "更新后的描述"
            }
        }


class KnowledgeBaseQueryReq(BaseModel):
    """知识库查询请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseQueryReq
    """
    page: int = Field(
        default=1,
        ge=1,
        description="页码（从 1 开始）"
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="size",
        description="每页数量"
    )
    keyword: Optional[str] = Field(
        None,
        max_length=255,
        alias="name",
        description="搜索关键词（模糊匹配知识库名称或描述）"
    )
    type: Optional[RagType] = Field(
        None,
        description="按 RAG 类型筛选"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 10,
                "name": "测试",
                "type": "DOCUMENT"
            }
        }


class FileInfo(BaseModel):
    """文件信息

    对应 Java: com.datamate.rag.indexer.interfaces.dto.AddFilesReq.FileInfo
    """
    id: str = Field(..., description="文件ID (对应 t_dm_dataset_files.id)")
    file_name: str = Field(alias="fileName", description="文件名")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "file-uuid-123",
                "fileName": "document.pdf"
            }
        }


class AddFilesReq(BaseModel):
    """添加文件请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.AddFilesReq
    """
    knowledge_base_id: Optional[str] = Field(None, alias="knowledgeBaseId", description="知识库ID（从路径参数获取，这里保留用于兼容）")
    process_type: ProcessType = Field(
        default=ProcessType.DEFAULT_CHUNK,
        alias="processType",
        description="分块处理类型"
    )
    chunk_size: int = Field(
        default=500,
        ge=50,
        le=2000,
        alias="chunkSize",
        description="分块大小"
    )
    overlap_size: int = Field(
        default=50,
        ge=0,
        le=500,
        alias="overlapSize",
        description="重叠大小"
    )
    delimiter: Optional[str] = Field(
        None,
        description="自定义分隔符（仅用于 CUSTOM_SEPARATOR_CHUNK）"
    )
    files: List[FileInfo] = Field(
        ...,
        min_length=1,
        description="文件列表"
    )

    @field_validator("delimiter")
    @classmethod
    def validate_delimiter(cls, v, info):
        """验证自定义分隔符"""
        if info.data.get("process_type") == ProcessType.CUSTOM_SEPARATOR_CHUNK and not v:
            raise ValueError("使用自定义分隔符分块时，delimiter 不能为空")
        return v

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "knowledgeBaseId": "kb-uuid-123",
                "processType": "DEFAULT_CHUNK",
                "chunkSize": 500,
                "overlapSize": 50,
                "files": [
                    {"id": "file-1", "fileName": "doc1.pdf"},
                    {"id": "file-2", "fileName": "doc2.pdf"}
                ]
            }
        }


class DeleteFilesReq(BaseModel):
    """删除文件请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.DeleteFilesReq
    """
    file_ids: List[str] = Field(
        ...,
        min_length=1,
        alias="ids",
        description="要删除的文件ID列表"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "ids": ["file-1", "file-2", "file-3"]
            }
        }


class RagFileReq(BaseModel):
    """RAG 文件查询请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.RagFileReq
    """
    page: int = Field(
        default=1,
        ge=1,
        description="页码"
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        alias="size",
        description="每页数量"
    )
    keyword: Optional[str] = Field(
        None,
        max_length=255,
        alias="fileName",
        description="搜索关键词（模糊匹配文件名）"
    )
    status: Optional[FileStatus] = Field(
        None,
        description="按状态筛选"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 10,
                "fileName": "测试",
                "status": "PROCESSED"
            }
        }


class RetrieveReq(BaseModel):
    """检索请求

    对应 Java: com.datamate.rag.indexer.interfaces.dto.RetrieveReq
    """
    query: str = Field(
        ...,
        min_length=1,
        description="检索查询文本"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        alias="topK",
        description="返回前 K 个结果"
    )
    threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="相似度阈值（仅返回分数大于等于该值的结果）"
    )
    knowledge_base_ids: List[str] = Field(
        ...,
        min_length=1,
        alias="knowledgeBaseIds",
        description="要检索的知识库ID列表"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "query": "什么是机器学习？",
                "topK": 5,
                "threshold": 0.7,
                "knowledgeBaseIds": ["kb-1", "kb-2"]
            }
        }


class PagingQuery(BaseModel):
    """分页查询请求

    对应 Java: com.datamate.common.interfaces.PagingQuery
    """
    page: int = Field(
        default=1,
        ge=1,
        description="页码（从 1 开始）"
    )
    size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="每页数量"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 10
            }
        }


class ChunkFilterQuery(BaseModel):
    """分块过滤查询请求

    支持分页和 Milvus 表达式过滤
    """
    page: int = Field(
        default=1,
        ge=1,
        description="页码（从 1 开始）"
    )
    size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="每页数量"
    )
    expr: Optional[str] = Field(
        None,
        description="Milvus 过滤表达式（如 id > \"1\" && text like \"%keyword%\"）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "size": 10,
                "expr": "id > \"1\""
            }
        }


class QueryRequest(BaseModel):
    """知识图谱查询请求"""
    knowledge_base_id: str = Field(..., description="知识库ID")
    query: str = Field(..., description="查询文本")

    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_base_id": "kb-uuid-123",
                "query": "什么是机器学习？"
            }
        }


class ChunkUpdateReq(BaseModel):
    """Chunk更新请求"""
    text: str = Field(..., min_length=1, description="分块文本内容")
    metadata: Optional[dict] = Field(default=None, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "这是修改后的分块内容...",
                "metadata": {
                    "fileName": "document.pdf",
                    "chunkIndex": 0,
                    "customField": "custom value"
                }
            }
        }
