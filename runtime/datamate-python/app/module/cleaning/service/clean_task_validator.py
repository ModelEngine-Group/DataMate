import re
from app.module.cleaning.schema import OperatorInstanceDto
from app.module.cleaning.exceptions import InvalidOperatorInputError, ExecutorTypeError


class CleanTaskValidator:
    """Validator for cleaning tasks and templates"""

    @staticmethod
    def check_input_and_output(instances: list[OperatorInstanceDto]) -> None:
        """Validate that operator input/output types are compatible"""
        if not instances:
            return

        for i in range(len(instances) - 1):
            current = instances[i]
            next_op = instances[i + 1]

            if not current.outputs:
                raise InvalidOperatorInputError(f"Operator {current.id} has no outputs defined")

            if not next_op.inputs:
                raise InvalidOperatorInputError(f"Operator {next_op.id} has no inputs defined")

            current_outputs = set(current.outputs.split(','))
            next_inputs = set(next_op.inputs.split(','))

            if not current_outputs.intersection(next_inputs):
                raise InvalidOperatorInputError(
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
                    if "datajuicer" in category.lower():
                        executor_types.add("datajuicer")
                    elif "datamate" in category.lower():
                        executor_types.add("datamate")

        if len(executor_types) > 1:
            raise ExecutorTypeError(
                "Cannot mix DataMate and DataJuicer operators in same task"
            )

        return executor_types.pop() if executor_types else "datamate"

    @staticmethod
    def check_task_id(task_id: str) -> None:
        """Validate task ID"""
        if not task_id:
            raise ValueError("Task ID cannot be empty")
