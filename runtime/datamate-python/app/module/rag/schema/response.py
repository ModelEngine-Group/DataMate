"""
RAG 模块响应 DTO

定义所有 API 响应的数据结构
与 Java 响应 DTO 保持字段一致
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from app.db.models.knowledge_gen import RagType, FileStatus


class ModelConfig(BaseModel):
    """模型配置信息

    对应 Java: com.datamate.common.setting.domain.entity.ModelConfig
    """
    id: str = Field(..., description="模型ID")
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="模型提供商")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "model-uuid-123",
                "name": "text-embedding-ada-002",
                "provider": "openai"
            }
        }


class KnowledgeBaseResp(BaseModel):
    """知识库响应

    对应 Java: com.datamate.rag.indexer.interfaces.dto.KnowledgeBaseResp
    """
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    type: RagType = Field(..., description="RAG类型")
    embedding_model: str = Field(alias="embeddingModel", description="嵌入模型ID")
    chat_model: Optional[str] = Field(None, alias="chatModel", description="聊天模型ID")
    file_count: Optional[int] = Field(None, alias="fileCount", description="文件数量")
    chunk_count: Optional[int] = Field(None, alias="chunkCount", description="分块数量")
    embedding: Optional[ModelConfig] = Field(None, description="嵌入模型配置")
    chat: Optional[ModelConfig] = Field(None, description="聊天模型配置")
    created_at: Optional[datetime] = Field(None, alias="createdAt", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="更新时间")
    created_by: Optional[str] = Field(None, alias="createdBy", description="创建人")
    updated_by: Optional[str] = Field(None, alias="updatedBy", description="更新人")

    class Config:
        populate_by_name = True  # 允许使用 snake_case 或 camelCase
        json_schema_extra = {
            "example": {
                "id": "kb-uuid-123",
                "name": "my_knowledge_base",
                "description": "我的知识库",
                "type": "DOCUMENT",
                "embeddingModel": "text-embedding-ada-002",
                "chatModel": "gpt-4",
                "fileCount": 10,
                "chunkCount": 150,
                "embedding": {
                    "id": "model-1",
                    "name": "text-embedding-ada-002",
                    "provider": "openai"
                }
            }
        }


class RagFileResp(BaseModel):
    """RAG 文件响应

    对应 Java: com.datamate.rag.indexer.domain.model.RagFile
    """
    id: str = Field(..., description="RAG文件ID")
    knowledge_base_id: str = Field(alias="knowledgeBaseId", description="知识库ID")
    file_name: str = Field(alias="fileName", description="文件名")
    file_id: str = Field(alias="fileId", description="原始文件ID")
    chunk_count: Optional[int] = Field(None, alias="chunkCount", description="分块数量")
    metadata: Optional[dict] = Field(None, description="元数据")
    status: FileStatus = Field(..., description="处理状态")
    err_msg: Optional[str] = Field(None, alias="errMsg", description="错误信息")
    created_at: Optional[datetime] = Field(None, alias="createdAt", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="更新时间")
    created_by: Optional[str] = Field(None, alias="createdBy", description="创建人")
    updated_by: Optional[str] = Field(None, alias="updatedBy", description="更新人")

    class Config:
        populate_by_name = True  # 允许使用 snake_case 或 camelCase
        json_schema_extra = {
            "example": {
                "id": "rag-file-uuid-123",
                "knowledgeBaseId": "kb-uuid-123",
                "fileName": "document.pdf",
                "fileId": "file-uuid-456",
                "chunkCount": 15,
                "metadata": {"size": 1024, "format": "pdf"},
                "status": "PROCESSED",
                "createdAt": "2025-01-01T00:00:00"
            }
        }


class RagChunkResp(BaseModel):
    """RAG 分块响应

    对应 Milvus 查询结果
    """
    id: str = Field(..., description="分块ID")
    text: str = Field(..., description="分块文本")
    metadata: dict = Field(..., description="元数据")
    score: float = Field(..., description="相似度分数")
    distance: Optional[float] = Field(None, description="距离（可选）")

    class Config:
        populate_by_name = True  # 允许使用 snake_case 或 camelCase
        json_schema_extra = {
            "example": {
                "id": "chunk-uuid-123",
                "text": "这是文档的一个分块内容...",
                "metadata": {
                    "fileName": "document.pdf",
                    "chunkIndex": 0
                },
                "score": 0.95
            }
        }


class SearchResult(BaseModel):
    """检索结果

    对应 Java: io.milvus.v2.service.vector.response.SearchResp.SearchResult
    """
    id: str = Field(..., description="结果ID")
    score: float = Field(..., description="相似度分数")
    text: str = Field(..., description="文本内容")
    metadata: dict = Field(default_factory=dict, description="元数据")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "chunk-uuid-123",
                "score": 0.95,
                "text": "相关文档内容...",
                "metadata": {"file_name": "doc.pdf"}
            }
        }


class PagedResponse(BaseModel):
    """分页响应

    对应 Java: com.datamate.common.interfaces.PagedResponse
    """
    content: List[Any] = Field(..., description="数据列表")
    total_elements: int = Field(alias="totalElements", description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页数量")
    total_pages: int = Field(alias="totalPages", description="总页数")

    @classmethod
    def create(cls, content: List[Any], total_elements: int, page: int, size: int):
        """创建分页响应

        Args:
            content: 数据列表
            total_elements: 总记录数
            page: 当前页码
            size: 每页数量

        Returns:
            PagedResponse 实例
        """
        total_pages = (total_elements + size - 1) // size if size > 0 else 0
        return cls(
            content=content,
            total_elements=total_elements,
            page=page,
            size=size,
            total_pages=total_pages
        )

    class Config:
        populate_by_name = True  # 允许使用 snake_case 或 camelCase
        json_schema_extra = {
            "example": {
                "content": [],
                "totalElements": 100,
                "page": 1,
                "size": 10,
                "totalPages": 10
            }
        }
