from typing import Literal, List, Dict, Any, Optional
from datetime import datetime

from pydantic import Field, ConfigDict

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse


class SyncDatasetRequest(BaseResponseModel):
    """同步数据集请求模型"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="映射ID（mapping UUID）")
    batch_size: int = Field(50, ge=1, le=100, description="批处理大小", alias="batchSize")
    file_priority: Literal[0, 1] = Field(0, description="0 数据集为主，1 标注平台为主", alias="filePriority")
    label_priority: Literal[0, 1] = Field(0, description="0 数据集为主，1 标注平台为主", alias="labelPriority")
    sync_annotations: bool = Field(True, description="是否同步标注数据", alias="syncAnnotations")
    annotation_direction: Literal["ls_to_dm", "dm_to_ls", "bidirectional"] = Field(
        "bidirectional", 
        description="标注同步方向: ls_to_dm(Label Studio到数据集), dm_to_ls(数据集到Label Studio), bidirectional(双向)",
        alias="annotationDirection"
    )
    overwrite: bool = Field(
        True, 
        description="是否覆盖DataMate中的标注（基于时间戳比较）"
    )
    overwrite_labeling_project: bool = Field(
        True, 
        description="是否覆盖Label Studio中的标注（基于时间戳比较）",
        alias="overwriteLabelingProject"
    )

class SyncDatasetResponse(BaseResponseModel):
    """同步数据集响应模型"""
    id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="同步状态")
    synced_files: int = Field(..., description="已同步文件数量")
    total_files: int = Field(0, description="总文件数量")
    message: str = Field(..., description="响应消息")

class SyncDatasetResponseStd(StandardResponse[SyncDatasetResponse]):
    pass


class SyncAnnotationsRequest(BaseResponseModel):
    """同步标注请求模型
    
    使用camelCase作为API接口字段名（通过alias），但Python代码内部使用snake_case。
    Pydantic会自动处理两种格式的转换。
    """
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="映射ID（mapping UUID）")
    batch_size: int = Field(50, ge=1, le=100, description="批处理大小", alias="batchSize")
    direction: Literal["ls_to_dm", "dm_to_ls", "bidirectional"] = Field(
        "bidirectional", 
        description="同步方向: ls_to_dm(Label Studio到数据集), dm_to_ls(数据集到Label Studio), bidirectional(双向)"
    )
    overwrite: bool = Field(
        True, 
        description="是否覆盖DataMate中的标注（基于时间戳比较）。True时，如果Label Studio的标注更新时间更新，则覆盖DataMate的标注"
    )
    overwrite_labeling_project: bool = Field(
        True, 
        description="是否覆盖Label Studio中的标注（基于时间戳比较）。True时，如果DataMate的标注更新时间更新，则覆盖Label Studio的标注",
        alias="overwriteLabelingProject"
    )


class TagInfo(BaseResponseModel):
    """标注信息结构（不包含时间戳，时间戳存储在文件级别的tags_updated_at字段）"""
    from_name: str = Field(..., description="标注工具名称")
    to_name: str = Field(..., description="目标对象名称")
    type: str = Field(..., description="标注类型")
    values: Dict[str, Any] = Field(..., description="标注值")


class SyncAnnotationsResponse(BaseResponseModel):
    """同步标注响应模型"""
    id: str = Field(..., description="映射UUID")
    status: str = Field(..., description="同步状态: success/partial/error")
    synced_to_dm: int = Field(0, description="同步到数据集的标注数量")
    synced_to_ls: int = Field(0, description="同步到Label Studio的标注数量")
    skipped: int = Field(0, description="跳过的标注数量")
    failed: int = Field(0, description="失败的标注数量")
    conflicts_resolved: int = Field(0, description="解决的冲突数量")
    message: str = Field(..., description="响应消息")


class SyncAnnotationsResponseStd(StandardResponse[SyncAnnotationsResponse]):
    pass