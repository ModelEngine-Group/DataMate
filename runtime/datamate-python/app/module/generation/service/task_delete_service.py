"""
任务删除服务 - 负责任务的删除操作
"""
from typing import List

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)


class TaskDeleteService:
    """任务删除服务 - 负责任务的删除操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_task(self, task_id: str) -> None:
        """
        删除任务及其所有关联数据

        Args:
            task_id: 任务 ID
        """
        task = await self._get_task(task_id)
        if not task:
            raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND)

        file_ids = await self._get_file_instance_ids(task_id)

        if file_ids:
            await self._delete_synthesis_data_by_files(file_ids)
            await self._delete_chunks_by_files(file_ids)
            await self._delete_file_instances(file_ids)

        await self.db.delete(task)
        await self.db.commit()

    async def delete_file_task(self, task_id: str, file_id: str) -> None:
        """
        删除文件任务并更新任务统计

        Args:
            task_id: 任务 ID
            file_id: 文件任务 ID
        """
        task = await self._get_task(task_id)
        if not task:
            raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND)

        file_task = await self._get_file_task(file_id)
        if not file_task:
            raise BusinessError(ErrorCodes.GENERATION_FILE_NOT_FOUND)

        await self._delete_synthesis_data_by_files([file_id])
        await self._delete_chunks_by_files([file_id])
        await self.db.delete(file_task)

        self._decrement_file_count(task)
        await self.db.commit()

    async def delete_chunk(self, chunk_id: str) -> None:
        """
        删除切片及其关联的合成数据

        Args:
            chunk_id: 切片 ID
        """
        chunk = await self._get_chunk(chunk_id)
        if not chunk:
            raise BusinessError(ErrorCodes.GENERATION_CHUNK_NOT_FOUND)

        await self._delete_synthesis_data_by_chunk(chunk_id)
        await self._delete_chunk(chunk_id)
        await self.db.commit()

    async def delete_synthesis_data_by_chunk(self, chunk_id: str) -> int:
        """
        删除切片下的所有合成数据

        Args:
            chunk_id: 切片 ID

        Returns:
            删除的记录数
        """
        result = await self._delete_synthesis_data_by_chunk(chunk_id)
        deleted = int(getattr(result, "rowcount", 0) or 0)
        await self.db.commit()
        return deleted

    async def batch_delete_synthesis_data(self, ids: List[str]) -> int:
        """
        批量删除合成数据

        Args:
            ids: 合成数据 ID 列表

        Returns:
            删除的记录数
        """
        if not ids:
            return 0
        result = await self.db.execute(
            delete(SynthesisData).where(SynthesisData.id.in_(ids))
        )
        deleted = int(getattr(result, "rowcount", 0) or 0)
        await self.db.commit()
        return deleted

    async def delete_chunks_batch(self, chunk_ids: List[str]) -> None:
        """
        批量删除切片

        Args:
            chunk_ids: 切片 ID 列表
        """
        for chunk_id in chunk_ids:
            chunk = await self._get_chunk(chunk_id)
            if chunk:
                await self._delete_synthesis_data_by_chunk(chunk_id)
                await self._delete_chunk(chunk_id)
        await self.db.commit()

    async def delete_chunks_by_file(self, file_id: str) -> None:
        """
        按文件任务维度删除切片

        Args:
            file_id: 文件任务 ID
        """
        await self._delete_synthesis_data_by_files([file_id])
        await self._delete_chunks_by_files([file_id])
        await self.db.commit()

    async def delete_chunks_by_task(self, task_id: str) -> None:
        """
        按任务维度删除切片

        Args:
            task_id: 任务 ID
        """
        file_ids = await self._get_file_instance_ids(task_id)
        if file_ids:
            await self._delete_synthesis_data_by_files(file_ids)
            await self._delete_chunks_by_files(file_ids)
        await self.db.commit()

    async def _get_task(self, task_id: str) -> DataSynthInstance | None:
        """获取任务"""
        return await self.db.get(DataSynthInstance, task_id)

    async def _get_file_task(self, file_id: str) -> DataSynthesisFileInstance | None:
        """获取文件任务"""
        return await self.db.get(DataSynthesisFileInstance, file_id)

    async def _get_chunk(self, chunk_id: str) -> DataSynthesisChunkInstance | None:
        """获取切片"""
        return await self.db.get(DataSynthesisChunkInstance, chunk_id)

    async def _get_file_instance_ids(self, task_id: str) -> List[str]:
        """获取任务下的所有文件任务 ID"""
        result = await self.db.execute(
            select(DataSynthesisFileInstance.id).where(
                DataSynthesisFileInstance.synthesis_instance_id == task_id
            )
        )
        return [row[0] for row in result.all()]

    def _decrement_file_count(self, task: DataSynthInstance) -> None:
        """递减任务的文件数量"""
        if task.total_files and task.total_files > 0:
            task.total_files -= 1
            if task.total_files < 0:
                task.total_files = 0

    async def _delete_synthesis_data_by_files(self, file_ids: List[str]) -> None:
        """批量删除文件任务下的合成数据"""
        await self.db.execute(
            delete(SynthesisData).where(
                SynthesisData.synthesis_file_instance_id.in_(file_ids)
            )
        )

    async def _delete_synthesis_data_by_chunk(self, chunk_id: str) -> None:
        """删除切片下的合成数据"""
        await self.db.execute(
            delete(SynthesisData).where(SynthesisData.chunk_instance_id == chunk_id)
        )

    async def _delete_chunks_by_files(self, file_ids: List[str]) -> None:
        """批量删除文件任务下的切片"""
        await self.db.execute(
            delete(DataSynthesisChunkInstance).where(
                DataSynthesisChunkInstance.synthesis_file_instance_id.in_(file_ids)
            )
        )

    async def _delete_chunk(self, chunk_id: str) -> None:
        """删除切片"""
        await self.db.execute(
            delete(DataSynthesisChunkInstance).where(
                DataSynthesisChunkInstance.id == chunk_id
            )
        )

    async def _delete_file_instances(self, file_ids: List[str]) -> None:
        """批量删除文件任务"""
        await self.db.execute(
            delete(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.id.in_(file_ids)
            )
        )
