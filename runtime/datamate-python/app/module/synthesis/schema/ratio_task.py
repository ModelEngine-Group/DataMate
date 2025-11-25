from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from app.core.logging import get_logger
from app.module.shared.schema.common import TaskStatus

logger = get_logger(__name__)

class LabelFilter(BaseModel):
    label: Optional[str] = Field(..., description="标签")
    value: Optional[str] = Field(None, description="标签值")

class FilterCondition(BaseModel):
    date_range: Optional[str] = Field(None, description="数据范围", alias="dateRange")
    label: Optional[LabelFilter] = Field(None, description="标签")

    @field_validator("date_range")
    @classmethod
    def validate_date_range(cls, v: Optional[str]) -> Optional[str]:
        # ensure it's a numeric string if provided
        if not v:
            return v
        try:
            int(v)
            return v
        except (ValueError, TypeError) as e:
            raise ValueError("date_range must be a numeric string")

    class Config:
        # allow population by field name when constructing model programmatically
        validate_by_name = True


class RatioConfigItem(BaseModel):
    dataset_id: str = Field(..., alias="datasetId", description="数据集id")
    counts: str = Field(..., description="数量")
    filter_conditions: FilterCondition = Field(..., alias="filterConditions", description="过滤条件")

    @field_validator("counts")
    @classmethod
    def validate_counts(cls, v: str) -> str:
        # ensure it's a numeric string
        try:
            int(v)
        except Exception:
            raise ValueError("counts must be a numeric string")
        return v


class CreateRatioTaskRequest(BaseModel):
    name: str = Field(..., description="名称")
    description: Optional[str] = Field(None, description="描述")
    totals: str = Field(..., description="目标数量")
    config: List[RatioConfigItem] = Field(..., description="配比设置列表")

    @field_validator("totals")
    @classmethod
    def validate_totals(cls, v: str) -> str:
        try:
            iv = int(v)
            if iv < 0:
                raise ValueError("totals must be >= 0")
        except Exception:
            raise ValueError("totals must be a numeric string")
        return v


class TargetDatasetInfo(BaseModel):
    id: str
    name: str
    datasetType: str
    status: str


class CreateRatioTaskResponse(BaseModel):
    # task info
    id: str
    name: str
    description: Optional[str] = None
    totals: int
    status: TaskStatus
    # echoed config
    config: List[RatioConfigItem]
    # created dataset
    targetDataset: TargetDatasetInfo


class RatioTaskItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: Optional[str] = None
    totals: Optional[int] = None
    target_dataset_id: Optional[str] = None
    target_dataset_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PagedRatioTaskResponse(BaseModel):
    content: List[RatioTaskItem]
    totalElements: int
    totalPages: int
    page: int
    size: int


class RatioTaskDetailResponse(BaseModel):
    """Detailed response for a ratio task."""
    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    status: str = Field(..., description="任务状态")
    totals: int = Field(..., description="目标总数")
    config: List[Dict[str, Any]] = Field(..., description="配比配置")
    target_dataset: Dict[str, Any] = Field(..., description="目标数据集信息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
