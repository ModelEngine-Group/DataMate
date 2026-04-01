"""
任务命令服务 - 负责任务的创建操作
"""
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import transaction
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    save_synthesis_task,
)
from app.db.models.dataset_management import DatasetFiles
from app.module.generation.schema.generation import CreateSynthesisTaskRequest


class TaskCreateService:
    """任务创建服务 - 负责任务的创建操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, request: CreateSynthesisTaskRequest) -> DataSynthInstance:
        """
        创建数据合成任务

        Args:
            request: 创建任务请求

        Returns:
            创建的任务实例
        """
        dataset_files = await self._query_source_files(request.source_file_id)
        request.source_file_id = [str(f.id) for f in dataset_files]

        async with transaction(self.db):
            task = await save_synthesis_task(self.db, request)
            await self._create_file_instances(task.id, dataset_files)

        return task

    async def _query_source_files(self, file_ids: List[str]) -> List[DatasetFiles]:
        """
        查询源文件列表

        Args:
            file_ids: 文件 ID 列表

        Returns:
            源文件列表
        """
        if not file_ids:
            return []
        result = await self.db.execute(
            select(DatasetFiles).where(DatasetFiles.id.in_(file_ids))
        )
        return list(result.scalars().all())

    async def _create_file_instances(
        self, task_id: str, dataset_files: List[DatasetFiles]
    ) -> None:
        """
        创建文件任务实例

        Args:
            task_id: 任务 ID
            dataset_files: 源文件列表
        """
        if not dataset_files:
            return

        file_instances = [
            DataSynthesisFileInstance(
                id=str(uuid.uuid4()),
                synthesis_instance_id=task_id,
                file_name=f.file_name,
                source_file_id=str(f.id),
                status="pending",
                total_chunks=0,
                processed_chunks=0,
                created_by="system",
                updated_by="system",
            )
            for f in dataset_files
        ]
        self.db.add_all(file_instances)
