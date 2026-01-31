"""
Operator Repository
算子数据访问层
"""
import json
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.operator import Operator
from app.module.operator.schema import OperatorDto


class OperatorRepository:
    """算子数据访问层"""

    def __init__(self, model: Operator):
        self.model = model

    async def find_all(self, db: AsyncSession) -> List[Operator]:
        """查询所有算子"""
        result = await db.execute(select(Operator))
        return result.scalars().all()

    async def insert(self, dto: OperatorDto, db: AsyncSession) -> None:
        """插入算子"""
        entity = Operator(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            version=dto.version,
            inputs=dto.inputs,
            outputs=dto.outputs,
            runtime=dto.runtime,
            settings=dto.settings,
            file_name=dto.file_name,
            file_size=dto.file_size,
            metrics=dto.metrics,
            usage_count=dto.usage_count or 0,
            is_star=dto.is_star or False,
        )
        db.add(entity)

    async def update(self, dto: OperatorDto, db: AsyncSession) -> None:
        """更新算子"""
        await db.execute(
            update(Operator)
            .where(Operator.id == dto.id)
            .values(
                name=dto.name,
                description=dto.description,
                version=dto.version,
                inputs=dto.inputs,
                outputs=dto.outputs,
                runtime=dto.runtime,
                settings=dto.settings,
                file_name=dto.file_name,
                file_size=dto.file_size,
                metrics=dto.metrics,
                is_star=dto.is_star,
                updated_at=datetime.utcnow(),
            )
        )

    async def delete(self, operator_id: str, db: AsyncSession) -> None:
        """删除算子"""
        entity = await db.get(Operator, operator_id)
        if entity:
            await db.delete(entity)

    async def count_by_star(self, is_star: bool, db: AsyncSession) -> int:
        """统计收藏算子数量"""
        result = await db.execute(
            select(text("COUNT(*)"))
            .select_from(Operator)
            .where(Operator.is_star == is_star)
        )
        return result.scalar() or 0

    async def operator_in_template(self, operator_id: str, db: AsyncSession) -> bool:
        """检查算子是否在模板中"""
        result = await db.execute(
            text("""
                SELECT COUNT(*) FROM t_operator_instance oi
                JOIN t_clean_template t ON oi.instance_id = t.id
                WHERE oi.operator_id = :operator_id
            """),
            {"operator_id": operator_id}
        )
        return (result.scalar() or 0) > 0

    async def operator_in_unstop_task(self, operator_id: str, db: AsyncSession) -> bool:
        """检查算子是否在未完成的任务中"""
        result = await db.execute(
            text("""
                SELECT COUNT(*) FROM t_operator_instance oi
                JOIN t_clean_task t ON oi.instance_id = t.id
                WHERE oi.operator_id = :operator_id AND t.status != 'COMPLETED'
            """),
            {"operator_id": operator_id}
        )
        return (result.scalar() or 0) > 0

    async def increment_usage_count(
        self,
        operator_ids: List[str],
        db: AsyncSession
    ) -> None:
        """增加算子使用次数"""
        if not operator_ids:
            return
        await db.execute(
            update(Operator)
            .where(Operator.id.in_(operator_ids))
            .values(
                usage_count=Operator.usage_count + 1,
                updated_at=datetime.now(timezone.utc),
            )
        )
