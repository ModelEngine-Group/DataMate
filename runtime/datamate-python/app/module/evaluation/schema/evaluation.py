from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from app.core.logging import get_logger
from app.module.shared.schema.common import TaskStatus

logger = get_logger(__name__)

class EvaluationConfig(BaseModel):
    """评估配置项"""
    model_id: str = Field(..., alias="modelId", description="模型id")
    model_name: str = Field(..., alias="modelName", description="模型名称")
    base_url: str = Field(..., alias="baseUrl", description="接口地址")


class CreateEvaluationTaskRequest(BaseModel):
    """创建评估任务请求"""
    name: str = Field(..., description="评估任务名称")
    description: Optional[str] = Field(None, description="评估任务描述")
    task_type: str = Field(..., alias="taskType", description="评估任务类型：QA/QUALITY/COMPATIBILITY/VALUE")
    source_type: str = Field(..., alias="sourceType", description="待评估对象类型：DATASET/SYNTHESIS")
    source_id: str = Field(..., alias="sourceId", description="待评估对象ID")
    source_name: str = Field(..., alias="sourceName", description="待评估对象名称")
    eval_method: str = Field("AUTO", alias="evalMethod", description="评估提示词")
    eval_prompt: str = Field(..., alias="evalPrompt", description="评估提示词")
    eval_config: EvaluationConfig = Field(..., alias="evalConfig", description="评估配置项列表")


class EvaluationTaskItem(BaseModel):
    """评估任务列表项"""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    task_type: Optional[str] = Field(..., alias="taskType", description="任务类型")
    source_type: Optional[str] = Field(..., alias="sourceType", description="数据源类型")
    source_id: Optional[str] = Field(..., alias="sourceId", description="数据源ID")
    source_name: Optional[str] = Field(None, alias="sourceName", description="数据源名称")
    status: TaskStatus = Field(..., description="任务状态")
    eval_process: Optional[float] = Field(0, alias="evalProcess", description="评估进度")
    created_at: Optional[str] = Field(None, alias="createdAt", description="创建时间")
    updated_at: Optional[str] = Field(None, alias="updatedAt", description="更新时间")


class PagedEvaluationTaskResponse(BaseModel):
    """分页评估任务响应"""
    content: List[EvaluationTaskItem]
    total_elements: int = Field(..., alias="totalElements")
    total_pages: int = Field(..., alias="totalPages")
    page: int
    size: int


class EvaluationTaskDetailResponse(EvaluationTaskItem):
    """评估任务详情响应"""
    eval_prompt: Optional[str] = Field(None, alias="evalPrompt", description="评估提示词")
    eval_config: Optional[Dict[str, Any]] = Field(None, alias="evalConfig", description="评估配置")
    eval_result: Optional[Dict[str, Any]] = Field(None, alias="evalResult", description="评估结果")


class EvaluationItemResponse(BaseModel):
    """评估条目响应"""
    id: str = Field(..., description="条目ID")
    task_id: str = Field(..., alias="taskId", description="任务ID")
    item_id: str = Field(..., alias="itemId", description="评估项ID")
    eval_score: float = Field(..., alias="evalScore", description="评估分数")
    eval_result: Optional[Dict[str, Any]] = Field(None, alias="evalResult", description="评估结果详情")
    status: str = Field(..., description="评估状态")
    created_at: Optional[str] = Field(None, alias="createdAt", description="创建时间")
    updated_at: Optional[str] = Field(None, alias="updatedAt", description="更新时间")
