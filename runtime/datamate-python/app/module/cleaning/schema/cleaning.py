from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.module.shared.schema.common import BaseResponseModel


class CleaningTaskStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class OperatorInstanceDto(BaseResponseModel):
    """Operator instance DTO for task or template"""
    id: str = Field(..., description="Operator ID")
    name: Optional[str] = Field(None, description="Operator name")
    description: Optional[str] = Field(None, description="Operator description")
    inputs: Optional[str] = Field(None, description="Input types: text/image/audio/video/multimodal")
    outputs: Optional[str] = Field(None, description="Output types: text/image/audio/video/multimodal")
    categories: Optional[List[str]] = Field(None, description="Category IDs")
    settings: Optional[str] = Field(None, description="算子设置（JSON）")
    overrides: Dict[str, Any] = Field(default_factory=dict, description="Operator parameter overrides")


class CleaningProcess(BaseResponseModel):
    """Task progress information (matches Java version)"""
    process: float = Field(..., description="Progress percentage")
    successRate: float = Field(..., description="Success rate percentage")
    totalFileNum: int = Field(..., description="Total file count")
    succeedFileNum: int = Field(..., description="Succeeded file count")
    failedFileNum: int = Field(..., description="Failed file count")
    finishedFileNum: int = Field(..., description="Finished file count")

    @classmethod
    def of(cls, total: int, succeed: int, failed: int) -> 'CleaningProcess':
        """Create progress info (matches Java version logic)"""
        finished_file_num = succeed + failed

        if total == 0:
            process = 0.0
        else:
            process = round(finished_file_num * 100.0 / total, 2)

        if finished_file_num == 0:
            success_rate = 0.0
        else:
            success_rate = round(succeed * 100.0 / finished_file_num, 2)

        return cls(
            process=process,
            successRate=success_rate,
            totalFileNum=total,
            succeedFileNum=succeed,
            failedFileNum=failed,
            finishedFileNum=finished_file_num,
        )


class CleaningTaskDto(BaseResponseModel):
    """Cleaning task DTO"""
    id: Optional[str] = Field(None, description="Task ID")
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    src_dataset_id: Optional[str] = Field(None, description="Source dataset ID")
    src_dataset_name: Optional[str] = Field(None, description="Source dataset name")
    dest_dataset_id: Optional[str] = Field(None, description="Destination dataset ID")
    dest_dataset_name: Optional[str] = Field(None, description="Destination dataset name")
    before_size: Optional[int] = Field(None, description="Data size before cleaning")
    after_size: Optional[int] = Field(None, description="Data size after cleaning")
    file_count: Optional[int] = Field(None, description="Total file count")
    retry_count: Optional[int] = Field(None, description="Retry count")
    status: Optional[str] = Field(None, description="Task status")
    template_id: Optional[str] = Field(None, description="Template ID if created from template")
    instance: Optional[List[OperatorInstanceDto]] = Field(None, description="Operator instances")
    progress: Optional[CleaningProcess] = Field(None, description="Task progress")
    created_at: Optional[datetime] = Field(None, description="Creation time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    finished_at: Optional[datetime] = Field(None, description="Finish time")


class CreateCleaningTaskRequest(BaseResponseModel):
    """Request to create cleaning task"""
    name: str = Field(..., description="Cleaning task name")
    description: str = Field(..., description="Cleaning task description")
    src_dataset_id: str = Field(..., description="Source dataset ID")
    src_dataset_name: str = Field(..., description="Source dataset name")
    dest_dataset_id: Optional[str] = Field(None, description="Destination dataset ID")
    dest_dataset_name: str = Field(..., description="Destination dataset name, creates new dataset if destDatasetId is empty")
    dest_dataset_type: str = Field(..., description="Destination dataset type: TEXT/IMAGE/VIDEO/AUDIO/OTHER")
    template_id: Optional[str] = Field(None, description="Template ID (alternative to instance)")
    instance: List[OperatorInstanceDto] = Field(default_factory=list, description="Operator list (alternative to templateId)")


class CleaningResultDto(BaseResponseModel):
    """Cleaning result DTO"""
    instance_id: Optional[str] = Field(None, description="Instance ID")
    src_file_id: Optional[str] = Field(None, description="Source file ID")
    dest_file_id: Optional[str] = Field(None, description="Destination file ID")
    src_name: Optional[str] = Field(None, description="Source file name")
    dest_name: Optional[str] = Field(None, description="Destination file name")
    src_type: Optional[str] = Field(None, description="Source file type")
    dest_type: Optional[str] = Field(None, description="Destination file type")
    src_size: Optional[int] = Field(None, description="Source file size")
    dest_size: Optional[int] = Field(None, description="Destination file size")
    status: Optional[str] = Field(None, description="Cleaning status")
    result: Optional[str] = Field(None, description="Cleaning result message")


class CleaningTaskLog(BaseResponseModel):
    """Task log entry"""
    level: str = Field(..., description="Log level: INFO, WARN, ERROR")
    message: str = Field(..., description="Log message")


class CleaningTemplateDto(BaseResponseModel):
    """Cleaning template DTO"""
    id: Optional[str] = Field(None, description="Template ID")
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    instance: List[OperatorInstanceDto] = Field(default_factory=list, description="Operator instances")
    created_at: Optional[datetime] = Field(None, description="Creation time")
    updated_at: Optional[datetime] = Field(None, description="Update time")


class CreateCleaningTemplateRequest(BaseResponseModel):
    """Request to create cleaning template"""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    instance: List[OperatorInstanceDto] = Field(..., description="Operator instances")


class UpdateCleaningTemplateRequest(BaseResponseModel):
    """Request to update cleaning template"""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    instance: List[OperatorInstanceDto] = Field(..., description="Operator instances")
