"""Service layer for Auto Annotation tasks"""
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.annotation_management import AutoAnnotationTask
from app.db.models.dataset_management import Dataset, DatasetFiles

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
            file_ids=request.file_ids,  # 存储用户选择的文件ID列表
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

        # 创建后附带 sourceDatasets 信息（通常只有一个原始数据集）
        resp = AutoAnnotationTaskResponse.model_validate(task)
        try:
            resp.source_datasets = await self._compute_source_datasets(db, task)
        except Exception:
            resp.source_datasets = [dataset_name] if dataset_name else [request.dataset_id]
        return resp

    async def list_tasks(self, db: AsyncSession) -> List[AutoAnnotationTaskResponse]:
        """获取未软删除的自动标注任务列表，按创建时间倒序。"""

        result = await db.execute(
            select(AutoAnnotationTask)
            .where(AutoAnnotationTask.deleted_at.is_(None))
            .order_by(AutoAnnotationTask.created_at.desc())
        )
        tasks: List[AutoAnnotationTask] = list(result.scalars().all())

        responses: List[AutoAnnotationTaskResponse] = []
        for task in tasks:
            resp = AutoAnnotationTaskResponse.model_validate(task)
            try:
                resp.source_datasets = await self._compute_source_datasets(db, task)
            except Exception:
                # 出错时降级为单个 datasetName/datasetId
                fallback_name = getattr(task, "dataset_name", None)
                fallback_id = getattr(task, "dataset_id", "")
                resp.source_datasets = [fallback_name] if fallback_name else [fallback_id]
            responses.append(resp)

        return responses

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

        resp = AutoAnnotationTaskResponse.model_validate(task)
        try:
            resp.source_datasets = await self._compute_source_datasets(db, task)
        except Exception:
            fallback_name = getattr(task, "dataset_name", None)
            fallback_id = getattr(task, "dataset_id", "")
            resp.source_datasets = [fallback_name] if fallback_name else [fallback_id]
        return resp

    async def _compute_source_datasets(
        self,
        db: AsyncSession,
        task: AutoAnnotationTask,
    ) -> List[str]:
        """根据任务的 file_ids 推断实际涉及到的所有数据集名称。

        - 如果存在 file_ids，则通过 t_dm_dataset_files 反查 dataset_id，再关联 t_dm_datasets 获取名称；
        - 如果没有 file_ids，则退回到任务上冗余的 dataset_name/dataset_id。
        """

        file_ids = task.file_ids or []
        if file_ids:
            stmt = (
                select(Dataset.name)
                .join(DatasetFiles, Dataset.id == DatasetFiles.dataset_id)
                .where(DatasetFiles.id.in_(file_ids))
                .distinct()
            )
            result = await db.execute(stmt)
            names = [row[0] for row in result.fetchall() if row[0]]
            if names:
                return names

        # 回退：只显示一个数据集
        if task.dataset_name:
            return [task.dataset_name]
        if task.dataset_id:
            return [task.dataset_id]
        return []

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

    async def update_task_files(
        self,
        db: AsyncSession,
        task_id: str,
        *,
        dataset_id: str,
        file_ids: List[str],
    ) -> Optional[AutoAnnotationTaskResponse]:
        """更新自动标注任务关联的数据集与文件列表。

        - 覆盖任务的 dataset_id 与 file_ids；
        - 将任务重置为 pending，供 worker 重新调度；
        - 保留已有的 output_path 与统计信息，确保同一任务始终复用同一个输出数据集，
          worker 内部会根据 output_path 中已有的 images 仅对新增文件执行自动标注。
        """

        result = await db.execute(
            select(AutoAnnotationTask).where(
                AutoAnnotationTask.id == task_id,
                AutoAnnotationTask.deleted_at.is_(None),
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return None

        now = datetime.now()

        task.dataset_id = dataset_id
        task.file_ids = file_ids or []

        # 将任务标记为待处理，让 worker 在同一个输出目录下仅对新增文件执行自动标注
        task.status = "pending"
        task.progress = 0
        task.updated_at = now

        db.add(task)
        await db.commit()
        await db.refresh(task)

        resp = AutoAnnotationTaskResponse.model_validate(task)
        try:
            resp.source_datasets = await self._compute_source_datasets(db, task)
        except Exception:
            fallback_name = getattr(task, "dataset_name", None)
            fallback_id = getattr(task, "dataset_id", "")
            resp.source_datasets = [fallback_name] if fallback_name else [fallback_id]
        return resp
