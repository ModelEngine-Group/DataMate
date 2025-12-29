import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator, ConfigDict
from pydantic.alias_generators import to_camel

from app.db.models.data_collection import CollectionTask, TaskExecution
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
