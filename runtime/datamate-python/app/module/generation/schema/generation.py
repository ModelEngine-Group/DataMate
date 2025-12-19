from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class TextSplitConfig(BaseModel):
    """文本切片配置"""
    chunk_size: int = Field(..., description="最大令牌数")
    chunk_overlap: int = Field(..., description="重叠令牌数")


class SynthesisConfig(BaseModel):
    """合成配置"""
    prompt_template: str = Field(..., description="合成提示模板")
    synthesis_count: int = Field(None, description="单个chunk合成的数据数量")
    temperature: Optional[float] = Field(None, description="温度参数")


class SynthesisType(Enum):
    """合成类型"""
    QA = "QA"
    COT = "COT"


class CreateSynthesisTaskRequest(BaseModel):
    """创建数据合成任务请求"""
    name: str = Field(..., description="合成任务名称")
    description: Optional[str] = Field(None, description="合成任务描述")
    model_id: str = Field(..., description="模型ID")
    source_file_id: list[str] = Field(..., description="原始文件ID列表")
    text_split_config: TextSplitConfig = Field(None, description="文本切片配置")
    synthesis_config: SynthesisConfig = Field(..., description="合成配置")
    synthesis_type: SynthesisType = Field(..., description="合成类型")

    @field_validator("description")
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        """前端如果传入空字符串，将其统一转换为 None，避免存库时看起来像有描述但实际上为空。"""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class DataSynthesisTaskItem(BaseModel):
    """数据合成任务列表/详情项"""
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    synthesis_type: str
    model_id: str
    progress: int
    result_data_location: Optional[str] = None
    text_split_config: Dict[str, Any]
    synthesis_config: Dict[str, Any]
    source_file_id: list[str]
    total_files: int
    processed_files: int
    total_chunks: int
    processed_chunks: int
    total_synthesis_data: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True


class PagedDataSynthesisTaskResponse(BaseModel):
    """分页数据合成任务响应"""
    content: List[DataSynthesisTaskItem]
    totalElements: int
    totalPages: int
    page: int
    size: int


class DataSynthesisFileTaskItem(BaseModel):
    """数据合成任务下的文件任务项"""
    id: str
    synthesis_instance_id: str
    file_name: str
    source_file_id: str
    target_file_location: str
    status: Optional[str] = None
    total_chunks: int
    processed_chunks: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        orm_mode = True


class PagedDataSynthesisFileTaskResponse(BaseModel):
    """分页数据合成任务文件任务响应"""
    content: List[DataSynthesisFileTaskItem]
    totalElements: int
    totalPages: int
    page: int
    size: int


class DataSynthesisChunkItem(BaseModel):
    """数据合成文件下的 chunk 记录"""
    id: str
    synthesis_file_instance_id: str
    chunk_index: Optional[int] = None
    chunk_content: Optional[str] = None
    chunk_metadata: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class PagedDataSynthesisChunkResponse(BaseModel):
    """分页 chunk 列表响应"""
    content: List[DataSynthesisChunkItem]
    totalElements: int
    totalPages: int
    page: int
    size: int


class SynthesisDataItem(BaseModel):
    """合成结果数据项"""
    id: str
    data: Optional[Dict[str, Any]] = None
    synthesis_file_instance_id: str
    chunk_instance_id: str

    class Config:
        orm_mode = True


class ChatRequest(BaseModel):
    """聊天请求参数"""
    model_id: str
    prompt: str


class SynthesisDataUpdateRequest(BaseModel):
    """单条合成数据 data 字段整体更新请求（前端传入完整 JSON，后端直接覆盖）"""
    data: Dict[str, Any] = Field(..., description="新的完整 JSON 对象，将覆盖原有 data 字段")


class BatchDeleteSynthesisDataRequest(BaseModel):
    """批量删除合成数据请求"""
    ids: List[str] = Field(..., description="需要删除的合成数据 ID 列表")


class BatchDeleteChunkInstancesRequest(BaseModel):
    """批量删除分块及其关联合成数据请求"""
    chunk_ids: List[str] = Field(..., description="需要删除的 chunk 实例 ID 列表")


class BatchDeleteChunkInstancesByFileRequest(BaseModel):
    """按文件任务维度删除 chunk 及其合成数据的请求"""
    file_id: str = Field(..., description="数据合成文件任务 ID")


class BatchDeleteChunkInstancesByTaskRequest(BaseModel):
    """按任务维度删除 chunk 及其合成数据的请求"""
    task_id: str = Field(..., description="数据合成任务 ID")


class SynthesisDataPatchItem(BaseModel):
    """用于前端展示/编辑的合成数据项（包含 chunk 与文件信息，可按需扩展）"""
    id: str
    data: Optional[Dict[str, Any]] = None
    chunk_instance_id: str
    synthesis_file_instance_id: str

    class Config:
        orm_mode = True
