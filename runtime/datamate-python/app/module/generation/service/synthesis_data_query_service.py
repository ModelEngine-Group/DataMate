"""
合成数据查询服务 - 负责合成数据相关的查询操作
"""
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.data_synthesis import (
    DataSynthesisFileInstance,
    SynthesisData,
)
from app.module.generation.schema.generation import (
    SynthesisDataItem,
    SynthesisDataPatchItem,
)


class SynthesisDataQueryService:
    """合成数据查询服务 - 负责合成数据相关的查询操作"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_chunk(self, chunk_id: str) -> List[SynthesisDataItem]:
        """
        根据切片 ID 查询所有合成数据

        Args:
            chunk_id: 切片 ID

        Returns:
            合成数据列表
        """
        result = await self.db.execute(
            select(SynthesisData).where(SynthesisData.chunk_instance_id == chunk_id)
        )
        rows = result.scalars().all()
        return [SynthesisDataItem.model_validate(row) for row in rows]

    async def list_by_file(self, file_id: str) -> List[SynthesisDataPatchItem]:
        """
        根据文件任务 ID 查询所有合成数据

        Args:
            file_id: 文件任务 ID

        Returns:
            合成数据列表
        """
        result = await self.db.execute(
            select(SynthesisData).where(
                SynthesisData.synthesis_file_instance_id == file_id
            )
        )
        rows = result.scalars().all()
        return [SynthesisDataPatchItem.model_validate(row) for row in rows]

    async def list_by_task(self, task_id: str) -> List[SynthesisDataPatchItem]:
        """
        根据任务 ID 查询所有合成数据

        Args:
            task_id: 任务 ID

        Returns:
            合成数据列表
        """
        result = await self.db.execute(
            select(SynthesisData).where(
                SynthesisData.synthesis_file_instance_id.in_(
                    select(DataSynthesisFileInstance.id).where(
                        DataSynthesisFileInstance.synthesis_instance_id == task_id
                    )
                )
            )
        )
        rows = result.scalars().all()
        return [SynthesisDataPatchItem.model_validate(row) for row in rows]

    async def update(self, data_id: str, data: dict) -> SynthesisDataItem | None:
        """
        更新合成数据

        Args:
            data_id: 数据 ID
            data: 新的数据内容

        Returns:
            更新后的数据，不存在则返回 None
        """
        record = await self.db.get(SynthesisData, data_id)
        if not record:
            return None
        record.data = data
        await self.db.commit()
        await self.db.refresh(record)
        return SynthesisDataItem.model_validate(record)
