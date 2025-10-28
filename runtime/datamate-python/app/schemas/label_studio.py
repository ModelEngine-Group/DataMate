from pydantic import Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from .common import BaseResponseModel

class LabelStudioProject(BaseResponseModel):
    """Label Studio项目模型"""
    id: int = Field(..., description="项目ID")
    title: str = Field(..., description="项目标题")
    description: Optional[str] = Field(None, description="项目描述")
    label_config: str = Field(..., description="标注配置")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class LabelStudioTaskData(BaseResponseModel):
    """Label Studio任务数据模型"""
    image: Optional[str] = Field(None, description="图像URL")
    text: Optional[str] = Field(None, description="文本内容")
    audio: Optional[str] = Field(None, description="音频URL")
    video: Optional[str] = Field(None, description="视频URL")
    filename: Optional[str] = Field(None, description="文件名")

class LabelStudioTask(BaseResponseModel):
    """Label Studio任务模型"""
    data: LabelStudioTaskData = Field(..., description="任务数据")
    project: Optional[int] = Field(None, description="项目ID")
    meta: Optional[Dict[str, Any]] = Field(None, description="元数据")

class LabelStudioCreateProjectRequest(BaseResponseModel):
    """创建Label Studio项目请求模型"""
    title: str = Field(..., description="项目标题")
    description: str = Field("", description="项目描述")
    label_config: str = Field(..., description="标注配置")
    
class LabelStudioCreateTaskRequest(BaseResponseModel):
    """创建Label Studio任务请求模型"""
    data: Dict[str, Any] = Field(..., description="任务数据")
    project: Optional[int] = Field(None, description="项目ID")