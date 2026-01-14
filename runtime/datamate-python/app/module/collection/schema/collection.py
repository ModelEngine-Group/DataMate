import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.data_collection import CollectionTask, TaskExecution, CollectionTemplate
from app.module.dataset.schema import DatasetTypeResponse
from app.module.dataset.schema.dataset import DatasetType
from app.module.shared.schema import TaskStatus


class SyncMode(str, Enum):
    ONCE = "ONCE"
    SCHEDULED = "SCHEDULED"

class CollectionConfig(BaseModel):
    parameter: Optional[dict] = Field(None, description="模板参数")
    reader: Optional[dict] = Field(None, description="reader参数")
    writer: Optional[dict] = Field(None, description="writer参数")
    job: Optional[dict] = Field(None, description="任务配置")

class CollectionTaskBase(BaseModel):
    id: str = Field(..., description="任务id")
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    target_path: str = Field(..., description="目标存放路径")
    config: CollectionConfig = Field(..., description="任务配置")
    template_id: str = Field(..., description="模板ID")
    template_name: Optional[str] = Field(None, description="模板名称")
    status: TaskStatus = Field(..., description="任务状态")
    sync_mode: SyncMode = Field(default=SyncMode.ONCE, description="同步方式")
    schedule_expression: Optional[str] = Field(None, description="调度表达式（cron）")
    retry_count: int = Field(default=3, description="重试次数")
    timeout_seconds: int = Field(default=3600, description="超时时间")
    last_execution_id: Optional[str] = Field(None, description="最后执行id")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建人")
    updated_by: Optional[str] = Field(None, description="更新人")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

class CollectionTaskCreate(BaseModel):
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    sync_mode: SyncMode = Field(default=SyncMode.ONCE, description="同步方式")
    schedule_expression: Optional[str] = Field(None, description="调度表达式（cron）")
    config: CollectionConfig = Field(..., description="任务配置")
    template_id: str = Field(..., description="模板ID")
    dataset_name: Optional[str] = Field(None, description="数据集名称")
    dataset_type: Optional[DatasetType] = Field(DatasetType.TEXT, description="数据集类型")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )

def converter_to_response(task: CollectionTask) -> CollectionTaskBase:
    return CollectionTaskBase(
        id=task.id,
        name=task.name,
        description=task.description,
        sync_mode=task.sync_mode,
        template_id=task.template_id,
        template_name=task.template_name,
        target_path=task.target_path,
        config=json.loads(task.config),
        schedule_expression=task.schedule_expression,
        status=task.status,
        retry_count=task.retry_count,
        timeout_seconds=task.timeout_seconds,
        last_execution_id=task.last_execution_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        created_by=task.created_by,
        updated_by=task.updated_by,
    )

def convert_for_create(task: CollectionTaskCreate, task_id: str) -> CollectionTask:
    return CollectionTask(
        id=task_id,
        name=task.name,
        description=task.description,
        sync_mode=task.sync_mode,
        template_id=task.template_id,
        target_path=f"/dataset/local/{task_id}",
        config=json.dumps(task.config.dict()),
        schedule_expression=task.schedule_expression,
        status=TaskStatus.PENDING.name
    )

def create_execute_record(task: CollectionTask) -> TaskExecution:
    execution_id = str(uuid.uuid4())
    return TaskExecution(
        id=execution_id,
        task_id=task.id,
        task_name=task.name,
        status=TaskStatus.RUNNING.name,
        started_at=datetime.now(),
        log_path=f"/flow/data-collection/{task.id}/{execution_id}.log"
    )


class TaskExecutionBase(BaseModel):
    id: str = Field(..., description="执行记录ID")
    task_id: str = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: Optional[str] = Field(None, description="执行状态")
    log_path: Optional[str] = Field(None, description="日志文件路径")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


def converter_execution_to_response(execution: TaskExecution) -> TaskExecutionBase:
    return TaskExecutionBase(
        id=execution.id,
        task_id=execution.task_id,
        task_name=execution.task_name,
        status=execution.status,
        log_path=execution.log_path,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        duration_seconds=execution.duration_seconds,
        error_message=execution.error_message,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
        created_by=execution.created_by,
        updated_by=execution.updated_by,
    )


class CollectionTemplateBase(BaseModel):
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    source_type: str = Field(..., description="源数据源类型")
    source_name: str = Field(..., description="源数据源名称")
    target_type: str = Field(..., description="目标数据源类型")
    target_name: str = Field(..., description="目标数据源名称")
    template_content: dict = Field(..., description="模板内容")
    built_in: Optional[bool] = Field(None, description="是否系统内置模板")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")
    updated_by: Optional[str] = Field(None, description="更新者")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


def converter_template_to_response(template: CollectionTemplate) -> CollectionTemplateBase:
    return CollectionTemplateBase(
        id=template.id,
        name=template.name,
        description=template.description,
        source_type=template.source_type,
        source_name=template.source_name,
        target_type=template.target_type,
        target_name=template.target_name,
        template_content=template.template_content,
        built_in=template.built_in,
        created_at=template.created_at,
        updated_at=template.updated_at,
        created_by=template.created_by,
        updated_by=template.updated_by,
    )
