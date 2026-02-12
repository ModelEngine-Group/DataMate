from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.db.models.cleaning import CleaningTask
from app.module.cleaning.schema import CleaningTaskDto


class CleaningTaskRepository:
    """Repository for cleaning task operations"""

    def __init__(self, model=None):
        self.model = model if model else CleaningTask

    async def find_tasks(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None
    ) -> List[CleaningTaskDto]:
        """Query cleaning tasks"""
        query = select(self.model)

        if status:
            query = query.where(self.model.status == status)

        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                self.model.name.ilike(keyword_pattern) | self.model.description.ilike(keyword_pattern)
            )

        query = query.order_by(self.model.created_at.desc())

        if page is not None and size is not None:
            offset = max((page - 1) * size, 0)
            query = query.offset(offset).limit(size)

        result = await db.execute(query)
        tasks = result.scalars().all()

        return [
            CleaningTaskDto(
                id=task.id,
                name=task.name,
                description=task.description,
                status=task.status,
                src_dataset_id=task.src_dataset_id,
                src_dataset_name=task.src_dataset_name,
                dest_dataset_id=task.dest_dataset_id,
                dest_dataset_name=task.dest_dataset_name,
                before_size=task.before_size,
                after_size=task.after_size,
                file_count=task.file_count,
                retry_count=task.retry_count,
                started_at=task.started_at,
                finished_at=task.finished_at,
                created_at=task.created_at
            )
            for task in tasks
        ]

    async def find_task_by_id(self, db: AsyncSession, task_id: str) -> Optional[CleaningTaskDto]:
        """Query task by ID"""
        query = select(self.model).where(self.model.id == task_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        return CleaningTaskDto(
            id=task.id,
            name=task.name,
            description=task.description,
            status=task.status,
            src_dataset_id=task.src_dataset_id,
            src_dataset_name=task.src_dataset_name,
            dest_dataset_id=task.dest_dataset_id,
            dest_dataset_name=task.dest_dataset_name,
            before_size=task.before_size,
            after_size=task.after_size,
            file_count=task.file_count,
            retry_count=task.retry_count,
            started_at=task.started_at,
            finished_at=task.finished_at,
            created_at=task.created_at
        )

    async def insert_task(self, db: AsyncSession, task: CleaningTaskDto) -> None:
        """Insert new task"""
        from app.db.models.cleaning import CleaningTask as CleaningTaskModel
        
        db_task = CleaningTaskModel(
            id=task.id,
            name=task.name,
            description=task.description,
            status=task.status,
            src_dataset_id=task.src_dataset_id,
            src_dataset_name=task.src_dataset_name,
            dest_dataset_id=task.dest_dataset_id,
            dest_dataset_name=task.dest_dataset_name,
            before_size=task.before_size,
            after_size=task.after_size,
            file_count=task.file_count,
            retry_count=task.retry_count
        )
        db.add(db_task)
        await db.flush()

    async def update_task(self, db: AsyncSession, task: CleaningTaskDto) -> None:
        """Update task"""
        query = select(CleaningTask).where(CleaningTask.id == task.id)
        result = await db.execute(query)
        db_task = result.scalar_one_or_none()

        if db_task:
            if task.status:
                db_task.status = task.status
            if task.started_at:
                db_task.started_at = task.started_at
            if task.finished_at:
                db_task.finished_at = task.finished_at
            if task.retry_count is not None:
                db_task.retry_count = task.retry_count

            await db.flush()

    async def delete_task_by_id(self, db: AsyncSession, task_id: str) -> None:
        """Delete task by ID"""
        query = delete(self.model).where(self.model.id == task_id)
        await db.execute(query)
        await db.flush()

    async def is_name_exist(self, db: AsyncSession, name: str) -> bool:
        """Check if task name exists"""
        query = select(func.count()).select_from(self.model).where(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one() > 0 if result else False
