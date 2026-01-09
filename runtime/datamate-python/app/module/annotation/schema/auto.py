"""Schemas for Auto Annotation tasks"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class AutoAnnotationConfig(BaseModel):
    """自动标注任务配置（与前端 payload 对齐）"""

    model_size: str = Field(alias="modelSize", description="模型规模: n/s/m/l/x")
    conf_threshold: float = Field(alias="confThreshold", description="置信度阈值 0-1")
    target_classes: List[int] = Field(
        default_factory=list,
        alias="targetClasses",
        description="目标类别ID列表，空表示全部类别",
    )
    output_dataset_name: Optional[str] = Field(
        default=None,
        alias="outputDatasetName",
        description="自动标注结果要写入的新数据集名称（可选）",
    )

    model_config = ConfigDict(populate_by_name=True)


class CreateAutoAnnotationTaskRequest(BaseModel):
    """创建自动标注任务的请求体，对齐前端 CreateAutoAnnotationDialog 发送的结构"""

    name: str = Field(..., min_length=1, max_length=255, description="任务名称")
    dataset_id: str = Field(..., alias="datasetId", description="数据集ID")
    config: AutoAnnotationConfig = Field(..., description="任务配置")
    file_ids: Optional[List[str]] = Field(None, alias="fileIds", description="要处理的文件ID列表，为空则处理数据集中所有图像")

    model_config = ConfigDict(populate_by_name=True)


class AutoAnnotationTaskResponse(BaseModel):
    """自动标注任务响应模型（列表/详情均可复用）"""

    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    dataset_id: str = Field(..., alias="datasetId", description="数据集ID")
    dataset_name: Optional[str] = Field(None, alias="datasetName", description="数据集名称")
    source_datasets: Optional[List[str]] = Field(
        default=None,
        alias="sourceDatasets",
        description="本任务实际处理涉及到的所有数据集名称列表",
    )
    config: Dict[str, Any] = Field(..., description="任务配置")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="任务进度 0-100")
    total_images: int = Field(..., alias="totalImages", description="总图片数")
    processed_images: int = Field(..., alias="processedImages", description="已处理图片数")
    detected_objects: int = Field(..., alias="detectedObjects", description="检测到的对象总数")
    output_path: Optional[str] = Field(None, alias="outputPath", description="输出路径")
    error_message: Optional[str] = Field(None, alias="errorMessage", description="错误信息")
    file_ids: Optional[List[str]] = Field(
        default=None,
        alias="fileIds",
        description="本次任务实际处理的文件ID列表，为空表示处理数据集全部文件",
    )
    created_at: datetime = Field(..., alias="createdAt", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="更新时间")
    completed_at: Optional[datetime] = Field(None, alias="completedAt", description="完成时间")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AutoAnnotationTaskListResponse(BaseModel):
    """自动标注任务列表响应，目前前端直接使用数组，这里预留分页结构"""

    content: List[AutoAnnotationTaskResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数")

    model_config = ConfigDict(populate_by_name=True)
