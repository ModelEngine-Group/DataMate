from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class RatioConfigItem(BaseModel):
    dataset_id: str = Field(..., alias="datasetId", description="数据集id")
    counts: str = Field(..., description="数量")
    filter_conditions: str = Field(..., description="过滤条件")

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
    ratio_method: str = Field(..., description="配比方式", alias="ratio_method")
    config: List[RatioConfigItem] = Field(..., description="配比设置列表")

    @field_validator("ratio_method")
    @classmethod
    def validate_ratio_method(cls, v: str) -> str:
        allowed = {"TAG", "DATASET"}
        if v not in allowed:
            raise ValueError(f"ratio_method must be one of {allowed}")
        return v

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
    ratio_method: str
    status: str
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
    ratio_method: Optional[str] = None
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
    ratio_method: str = Field(..., description="配比方式")
    config: List[Dict[str, Any]] = Field(..., description="配比配置")
    target_dataset: Dict[str, Any] = Field(..., description="目标数据集信息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
