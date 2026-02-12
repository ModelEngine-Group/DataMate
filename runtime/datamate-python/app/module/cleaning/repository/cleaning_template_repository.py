from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.db.models.cleaning import CleaningTemplate


class CleaningTemplateRepository:
    """Repository for cleaning template operations"""

    def __init__(self, model=None):
        self.model = model if model else CleaningTemplate

    async def find_all_templates(
        self,
        db: AsyncSession,
        keyword: Optional[str] = None
    ) -> List[CleaningTemplate]:
        """Query all templates"""
        query = select(self.model)

        if keyword:
            keyword_pattern = f"%{keyword}%"
            query = query.where(
                self.model.name.ilike(keyword_pattern) | self.model.description.ilike(keyword_pattern)
            )

        query = query.order_by(self.model.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    async def find_template_by_id(self, db: AsyncSession, template_id: str) -> Optional[CleaningTemplate]:
        """Query template by ID"""
        query = select(self.model).where(self.model.id == template_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def insert_template(self, db: AsyncSession, template: CleaningTemplate) -> None:
        """Insert new template"""
        db.add(template)
        await db.flush()

    async def update_template(self, db: AsyncSession, template: CleaningTemplate) -> None:
        """Update template"""
        query = select(self.model).where(self.model.id == template.id)
        result = await db.execute(query)
        db_template = result.scalar_one_or_none()

        if db_template:
            db_template.name = template.name
            db_template.description = template.description
            await db.flush()

    async def delete_template(self, db: AsyncSession, template_id: str) -> None:
        """Delete template"""
        query = delete(self.model).where(self.model.id == template_id)
        await db.execute(query)
        await db.flush()

    async def is_name_exist(self, db: AsyncSession, name: str) -> bool:
        """Check if template name exists"""
        query = select(func.count()).select_from(self.model).where(self.model.name == name)
        result = await db.execute(query)
        return result.scalar_one() > 0 if result else False
