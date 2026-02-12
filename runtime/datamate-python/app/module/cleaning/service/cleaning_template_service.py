import json
import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.core.logging import get_logger
from app.module.cleaning import UpdateCleaningTemplateRequest
from app.module.cleaning.repository import (
    CleaningTemplateRepository,
    OperatorInstanceRepository,
)
from app.module.cleaning.schema import (
    CleaningTemplateDto,
    CreateCleaningTemplateRequest,
    OperatorInstanceDto,
)
from app.module.cleaning.service.cleaning_task_validator import CleaningTaskValidator

logger = get_logger(__name__)


class CleaningTemplateService:
    """Service for managing cleaning templates"""

    def __init__(
        self,
        template_repo: CleaningTemplateRepository,
        operator_instance_repo: OperatorInstanceRepository,
        operator_service,
        validator: CleaningTaskValidator,
    ):
        self.template_repo = template_repo
        self.operator_instance_repo = operator_instance_repo
        self.operator_service = operator_service
        self.validator = validator

    async def get_templates(
        self,
        db: AsyncSession,
        keyword: str | None = None
    ) -> List[CleaningTemplateDto]:
        """Get all templates"""
        templates = await self.template_repo.find_all_templates(db, keyword)

        # Collect all operator IDs
        template_instances_map = {}
        for template in templates:
            instances = await self.operator_instance_repo.find_operator_by_instance_id(db, template.id)
            template_instances_map[template.id] = instances

        # Batch query all operators
        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None,
                                                                  is_star=None)
        operator_map = {op.id: op for op in all_operators}

        # Build result
        result = []
        for template in templates:
            template_dto = CleaningTemplateDto(
                id=template.id,
                name=template.name,
                description=template.description,
                instance=[],
                created_at=template.created_at,
                updated_at=template.updated_at,
            )

            instances = template_instances_map.get(template.id, [])
            for inst in instances:
                operator = operator_map.get(inst.operator_id)
                if operator:
                    operator_dto = OperatorInstanceDto(
                        id=operator.id,
                        name=operator.name,
                        description=operator.description,
                        inputs=operator.inputs,
                        outputs=operator.outputs,
                        settings=operator.settings,
                        categories=operator.categories,
                    )
                    if inst.settings_override:
                        try:
                            operator_dto.overrides = json.loads(inst.settings_override)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse settings for {inst.operator_id}: {e}")
                    template_dto.instance.append(operator_dto)

            result.append(template_dto)

        return result

    async def get_template(
        self,
        db: AsyncSession,
        template_id: str
    ) -> CleaningTemplateDto:
        """Get template by ID"""
        template = await self.template_repo.find_template_by_id(db, template_id)
        if not template:
            raise BusinessError(ErrorCodes.CLEANING_TEMPLATE_NOT_FOUND, template_id)

        template_dto = CleaningTemplateDto(
            id=template.id,
            name=template.name,
            description=template.description,
            instance=[],
            created_at=template.created_at,
            updated_at=template.updated_at,
        )

        instances = await self.operator_instance_repo.find_operator_by_instance_id(db, template_id)

        # Batch query operators
        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None,
                                                                  is_star=None)
        operator_map = {op.id: op for op in all_operators}

        for inst in instances:
            operator = operator_map.get(inst.operator_id)
            if operator:
                operator_dto = OperatorInstanceDto(
                    id=operator.id,
                    name=operator.name,
                    description=operator.description,
                    inputs=operator.inputs,
                    outputs=operator.outputs,
                    settings=operator.settings,
                    categories=operator.categories,
                )
                if inst.settings_override:
                    try:
                        operator_dto.overrides = json.loads(inst.settings_override)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse settings for {inst.operator_id}: {e}")
                template_dto.instance.append(operator_dto)

        return template_dto

    async def create_template(
        self,
        db: AsyncSession,
        request: CreateCleaningTemplateRequest
    ) -> CleaningTemplateDto:
        """Create new template"""
        from app.db.models.cleaning import CleaningTemplate

        await self.validator.check_template_name_duplication(db, request.name)
        self.validator.check_input_and_output(request.instance)
        self.validator.check_and_get_executor_type(request.instance)

        template_id = str(uuid.uuid4())
        template = CleaningTemplate(
            id=template_id,
            name=request.name,
            description=request.description,
        )

        await self.template_repo.insert_template(db, template)

        await self.operator_instance_repo.insert_instance(db, template_id, request.instance)

        return await self.get_template(db, template_id)

    async def update_template(
        self,
        db: AsyncSession,
        template_id: str,
        request: UpdateCleaningTemplateRequest
    ) -> CleaningTemplateDto:
        """Update template"""

        template = await self.template_repo.find_template_by_id(db, template_id)
        if not template:
            raise BusinessError(ErrorCodes.CLEANING_TEMPLATE_NOT_FOUND, template_id)

        template.name = request.name
        template.description = request.description

        await self.template_repo.update_template(db, template)
        await self.operator_instance_repo.delete_by_instance_id(db, template_id)

        await self.operator_instance_repo.insert_instance(db, template_id, request.instance)

        return await self.get_template(db, template_id)

    async def delete_template(self, db: AsyncSession, template_id: str) -> None:
        """Delete template"""
        await self.template_repo.delete_template(db, template_id)
        await self.operator_instance_repo.delete_by_instance_id(db, template_id)

    async def get_instance_by_template_id(
        self,
        db: AsyncSession,
        template_id: str
    ) -> List[OperatorInstanceDto]:
        """Get operator instances by template ID"""
        instances = await self.operator_instance_repo.find_operator_by_instance_id(db, template_id)

        # Batch query operators
        all_operators = await self.operator_service.get_operators(db=db, page=0, size=1000, categories=[], keyword=None,
                                                                  is_star=None)
        operator_map = {op.id: op for op in all_operators}

        result = []
        for inst in instances:
            operator = operator_map.get(inst.operator_id)
            if operator:
                operator_dto = OperatorInstanceDto(
                    id=operator.id,
                    name=operator.name,
                    description=operator.description,
                    inputs=operator.inputs,
                    outputs=operator.outputs,
                    settings=operator.settings,
                    categories=operator.categories,
                )
                if inst.settings_override:
                    try:
                        operator_dto.overrides = json.loads(inst.settings_override)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse settings for {inst.operator_id}: {e}")
                result.append(operator_dto)

        return result
