from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes
from app.module.cleaning.schema import OperatorInstanceDto
from app.module.operator.constants import CATEGORY_DATA_JUICER_ID, CATEGORY_DATAMATE_ID


class CleaningTaskValidator:
    """Validator for cleaning tasks and templates"""

    def __init__(self, task_repo=None, template_repo=None):
        self.task_repo = task_repo
        self.template_repo = template_repo

    async def check_task_name_duplication(self, db: AsyncSession, name: str) -> None:
        """Check if task name is duplicated"""
        if not name:
            raise BusinessError(ErrorCodes.CLEANING_NAME_DUPLICATED)
        if await self.task_repo.is_name_exist(db, name):
            raise BusinessError(ErrorCodes.CLEANING_NAME_DUPLICATED)

    async def check_template_name_duplication(self, db: AsyncSession, name: str) -> None:
        """Check if template name is duplicated"""
        if not name:
            raise BusinessError(ErrorCodes.CLEANING_TEMPLATE_NAME_DUPLICATED)
        if await self.template_repo.is_name_exist(db, name):
            raise BusinessError(ErrorCodes.CLEANING_TEMPLATE_NAME_DUPLICATED)

    @staticmethod
    def check_input_and_output(instances: list[OperatorInstanceDto]) -> None:
        """Validate that operator input/output types are compatible"""
        if not instances:
            return

        for i in range(len(instances) - 1):
            current = instances[i]
            next_op = instances[i + 1]

            if not current.outputs:
                raise BusinessError(
                    ErrorCodes.CLEANING_INVALID_OPERATOR_INPUT,
                    f"Operator {current.id} has no outputs defined"
                )

            if not next_op.inputs:
                raise BusinessError(
                    ErrorCodes.CLEANING_INVALID_OPERATOR_INPUT,
                    f"Operator {next_op.id} has no inputs defined"
                )

            current_outputs = set(current.outputs.split(','))
            next_inputs = set(next_op.inputs.split(','))

            if not current_outputs.intersection(next_inputs):
                raise BusinessError(
                    ErrorCodes.CLEANING_INVALID_OPERATOR_INPUT,
                    f"Operator {current.id} outputs {current.outputs} "
                    f"but operator {next_op.id} requires {next_op.inputs}"
                )

    @staticmethod
    def check_and_get_executor_type(instances: list[OperatorInstanceDto]) -> str:
        """Check operator categories and determine executor type (datamate/datajuicer)"""
        if not instances:
            return "datamate"

        executor_types = set()

        for instance in instances:
            if instance.categories:
                for category in instance.categories:
                    if CATEGORY_DATA_JUICER_ID in category.lower():
                        executor_types.add("default")
                    elif CATEGORY_DATAMATE_ID in category.lower():
                        executor_types.add("datamate")

        if len(executor_types) > 1:
            raise BusinessError(
                ErrorCodes.CLEANING_INVALID_EXECUTOR_TYPE,
                "Cannot mix DataMate and DataJuicer operators in same task"
            )

        return executor_types.pop() if executor_types else "datamate"

    @staticmethod
    def check_task_id(task_id: str) -> None:
        """Validate task ID"""
        if not task_id:
            raise BusinessError(ErrorCodes.CLEANING_TASK_ID_REQUIRED)
