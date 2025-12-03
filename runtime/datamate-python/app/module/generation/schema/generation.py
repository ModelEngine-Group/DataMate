from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


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
    description: str = Field(None, description="合成任务描述")
    model_id: str = Field(..., description="模型ID")
    source_file_id: list[str] = Field(..., description="原始文件ID列表")
    text_split_config: TextSplitConfig = Field(None, description="文本切片配置")
    synthesis_config: SynthesisConfig = Field(..., description="合成配置")
    synthesis_type: SynthesisType = Field(..., description="合成类型")


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

class ChatRequest(BaseModel):
    """聊天请求参数"""
    model_id: str
    prompt: str
