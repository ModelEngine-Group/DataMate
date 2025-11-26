from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TextSplitConfig(BaseModel):
    """文本切片配置"""
    max_characters: int = Field(50000, description="文件最大字符数，超过截断，-1不处理", ge=-1)
    chunk_size: int = Field(800, description="文本块大小", gt=0)
    chunk_overlap: int = Field(200, description="文本块重叠度", ge=0)

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v


class QAGenerationConfig(BaseModel):
    """QA生成配置"""
    max_questions: int = Field(3, description="每个文本块最大问题数量", ge=1, le=10)
    temperature: float = Field(0.3, description="模型生成时的创造力，值越低创造力越低", ge=0.0, le=2.0)
    model: str = Field("gpt-5-nano", description="使用的模型名称")


class CreateQATaskRequest(BaseModel):
    """创建QA生成任务请求
    
    新版本支持:
    - 通过 file_ids 列表指定要处理的文件（来自 t_dm_dataset_files）
    - 自动检测并支持 .txt, .md, .json 格式
    - 自定义 extra_prompt 插入到 LLM 提示词中
    """
    name: str = Field(..., description="任务名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="任务描述", max_length=1000)
    source_file_ids: List[str] = Field(..., alias="sourceFileIds", description="源文件ID列表（t_dm_dataset_files.id）", min_length=1)
    extra_prompt: Optional[str] = Field(None, alias="extraPrompt", description="用户自定义提示词，会插入到LLM Prompt中", max_length=2000)
    text_split_config: TextSplitConfig = Field(..., alias="textSplitConfig", description="文本切片配置")
    qa_generation_config: QAGenerationConfig = Field(..., alias="qaGenerationConfig", description="QA生成配置")
    llm_api_key: str = Field(..., alias="llmApiKey", description="LLM API密钥")
    llm_base_url: str = Field(..., alias="llmBaseUrl", description="LLM Base URL")

    class Config:
        populate_by_name = True


class TargetDatasetInfo(BaseModel):
    """目标数据集信息"""
    id: str
    name: str
    datasetType: str
    status: str


class CreateQATaskResponse(BaseModel):
    """创建QA生成任务响应"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: str = Field(..., description="任务状态")
    source_file_ids: List[str] = Field(..., description="源文件ID列表")
    target_dataset_id: str = Field(..., description="目标数据集ID")
    text_split_config: TextSplitConfig = Field(..., description="文本切片配置")
    qa_generation_config: QAGenerationConfig = Field(..., description="QA生成配置")
    targetDataset: TargetDatasetInfo = Field(..., description="目标数据集信息")
    created_at: Optional[str] = Field(None, description="创建时间")


class QATaskItem(BaseModel):
    """QA任务列表项"""
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    source_dataset_id: Optional[str] = None
    source_dataset_name: Optional[str] = None
    target_dataset_id: Optional[str] = None
    target_dataset_name: Optional[str] = None
    total_files: Optional[int] = None
    processed_files: Optional[int] = None
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    total_qa_pairs: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PagedQATaskResponse(BaseModel):
    """分页QA任务响应"""
    content: List[QATaskItem]
    totalElements: int
    totalPages: int
    page: int
    size: int


class QATaskDetailResponse(BaseModel):
    """QA任务详情响应"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: str = Field(..., description="任务状态: PENDING, RUNNING, COMPLETED, FAILED")
    source_dataset_id: str = Field(..., description="源数据集ID")
    target_dataset_id: Optional[str] = Field(None, description="目标数据集ID")
    text_split_config: Dict[str, Any] = Field(..., description="文本切片配置")
    qa_generation_config: Dict[str, Any] = Field(..., description="QA生成配置")
    source_dataset: Dict[str, Any] = Field(..., description="源数据集信息")
    target_dataset: Optional[Dict[str, Any]] = Field(None, description="目标数据集信息")
    total_files: Optional[int] = Field(None, description="总文件数")
    processed_files: Optional[int] = Field(None, description="已处理文件数")
    total_chunks: Optional[int] = Field(None, description="总文本块数")
    processed_chunks: Optional[int] = Field(None, description="已处理文本块数")
    total_qa_pairs: Optional[int] = Field(None, description="生成的QA对总数")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
