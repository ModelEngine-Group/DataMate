"""Service layer for Auto Annotation tasks"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.annotation_management import AutoAnnotationTask

from ..schema.auto import (
    CreateAutoAnnotationTaskRequest,
    AutoAnnotationTaskResponse,
)


class AutoAnnotationTaskService:
    """自动标注任务服务（仅管理任务元数据，真正执行由 runtime 负责）"""

    async def create_task(
        self,
        db: AsyncSession,
        request: CreateAutoAnnotationTaskRequest,
        dataset_name: Optional[str] = None,
        total_images: int = 0,
    ) -> AutoAnnotationTaskResponse:
        """创建自动标注任务，初始状态为 pending。

        这里仅插入任务记录，不负责真正执行 YOLO 推理，
        后续可以由调度器/worker 读取该表并更新进度。
        """

        now = datetime.now()

        task = AutoAnnotationTask(
            id=str(uuid4()),
            name=request.name,
            dataset_id=request.dataset_id,
            dataset_name=dataset_name,
            config=request.config.model_dump(by_alias=True),
            status="pending",
            progress=0,
            total_images=total_images,
            processed_images=0,
            detected_objects=0,
            created_at=now,
            updated_at=now,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return AutoAnnotationTaskResponse.model_validate(task)

    async def list_tasks(self, db: AsyncSession) -> List[AutoAnnotationTaskResponse]:
        """获取未软删除的自动标注任务列表，按创建时间倒序。"""

        result = await db.execute(
            select(AutoAnnotationTask)
            .where(AutoAnnotationTask.deleted_at.is_(None))
            .order_by(AutoAnnotationTask.created_at.desc())
        )
        tasks: List[AutoAnnotationTask] = list(result.scalars().all())
        return [AutoAnnotationTaskResponse.model_validate(t) for t in tasks]

    async def get_task(self, db: AsyncSession, task_id: str) -> Optional[AutoAnnotationTaskResponse]:
        result = await db.execute(
            select(AutoAnnotationTask).where(
                AutoAnnotationTask.id == task_id,
                AutoAnnotationTask.deleted_at.is_(None),
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return None
        return AutoAnnotationTaskResponse.model_validate(task)

    async def soft_delete_task(self, db: AsyncSession, task_id: str) -> bool:
        result = await db.execute(
            select(AutoAnnotationTask).where(
                AutoAnnotationTask.id == task_id,
                AutoAnnotationTask.deleted_at.is_(None),
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return False

        task.deleted_at = datetime.now()
        await db.commit()
        return True
