"""切片处理器模块 - 负责文本切片和持久化操作"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import (
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
)
from app.db.session import logger


class ChunkProcessor:
    """切片处理器"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def persist_chunks(
        self,
        synthesis_task: DataSynthInstance,
        file_task: DataSynthesisFileInstance,
        file_id: str,
        chunks: list[Any],
    ) -> int:
        """将切片结果保存到数据库。

        Args:
            synthesis_task: 合成任务实例
            file_task: 文件任务实例
            file_id: 原始文件ID
            chunks: 切片后的文档列表

        Returns:
            保存的切片数量
        """
        for idx, doc in enumerate(chunks, start=1):
            base_metadata = dict(getattr(doc, "metadata", {}) or {})
            base_metadata.update({
                "task_id": str(synthesis_task.id),
                "file_id": file_id
            })

            chunk_record = DataSynthesisChunkInstance(
                id=str(uuid.uuid4()),
                synthesis_file_instance_id=file_task.id,
                chunk_index=idx,
                chunk_content=doc.page_content,
                chunk_metadata=base_metadata,
            )
            self.db.add(chunk_record)

        file_task.total_chunks = len(chunks)
        file_task.status = "processing"

        await self.db.commit()
        await self.db.refresh(file_task)

        logger.info(f"Persisted {len(chunks)} chunks for file_task={file_task.id}")
        return len(chunks)

    async def load_chunk_batch(
        self,
        file_task_id: str,
        start_index: int,
        end_index: int,
    ) -> list[DataSynthesisChunkInstance]:
        """按索引范围加载指定文件任务下的一批切片记录。

        Args:
            file_task_id: 文件任务ID
            start_index: 起始索引（包含）
            end_index: 结束索引（包含）

        Returns:
            切片实例列表
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(DataSynthesisChunkInstance)
            .where(
                DataSynthesisChunkInstance.synthesis_file_instance_id == file_task_id,
                DataSynthesisChunkInstance.chunk_index >= start_index,
                DataSynthesisChunkInstance.chunk_index <= end_index,
            )
            .order_by(DataSynthesisChunkInstance.chunk_index.asc())
        )
        return list(result.scalars().all())

    async def count_chunks_for_file(self, synth_file_instance_id: str) -> int:
        """统计指定任务与文件下的切片总数。

        Args:
            synth_file_instance_id: 文件实例ID

        Returns:
            切片总数
        """
        from sqlalchemy import func, select

        result = await self.db.execute(
            select(func.count(DataSynthesisChunkInstance.id)).where(
                DataSynthesisChunkInstance.synthesis_file_instance_id == synth_file_instance_id
            )
        )
        return int(result.scalar() or 0)
