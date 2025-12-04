from enum import Enum

class BusinessErrorCode:
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code


class BusinessException(RuntimeError):
    def __init__(self, business_error_code: BusinessErrorCode):
        self.message = business_error_code.message
        self.error_code = business_error_code.error_code
        super().__init__(self.message)


class BusinessErrorCodeEnum(Enum):
    TASK_TYPE_ERROR = BusinessErrorCode("任务类型错误", "evaluation.0001")
