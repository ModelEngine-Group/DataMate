"""
Operator Market Exceptions
算子市场异常定义
"""
from enum import Enum
from typing import Optional


class OperatorErrorCode:
    """算子错误码"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code


class OperatorException(RuntimeError):
    """算子异常基类"""
    def __init__(self, operator_error_code: OperatorErrorCode):
        self.message = operator_error_code.message
        self.error_code = operator_error_code.error_code
        super().__init__(self.message)


class OperatorErrorCodeEnum(Enum):
    """算子错误码枚举"""
    FIELD_NOT_FOUND = OperatorErrorCode(
        "必填字段缺失", "OPERATOR_FIELD_NOT_FOUND"
    )
    SETTINGS_PARSE_FAILED = OperatorErrorCode(
        "设置解析失败", "OPERATOR_SETTINGS_PARSE_FAILED"
    )
    OPERATOR_IN_INSTANCE = OperatorErrorCode(
        "算子正在使用中", "OPERATOR_IN_INSTANCE"
    )
    CANT_DELETE_PREDEFINED_OPERATOR = OperatorErrorCode(
        "无法删除预定义算子", "CANT_DELETE_PREDEFINED_OPERATOR"
    )


class FieldNotFoundError(OperatorException):
    """必填字段缺失"""
    def __init__(self, field_name: str):
        super().__init__(
            OperatorErrorCodeEnum.FIELD_NOT_FOUND.value
        )
        self.message = f"Required field '{field_name}' is missing"
        self.field_name = field_name


class SettingsParseError(OperatorException):
    """设置解析失败"""
    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            OperatorErrorCodeEnum.SETTINGS_PARSE_FAILED.value
        )
        self.detail = detail


class OperatorInInstanceError(OperatorException):
    """算子正在使用中"""
    def __init__(self):
        super().__init__(
            OperatorErrorCodeEnum.OPERATOR_IN_INSTANCE.value
        )


class CannotDeletePredefinedOperatorError(OperatorException):
    """无法删除预定义算子"""
    def __init__(self):
        super().__init__(
            OperatorErrorCodeEnum.CANT_DELETE_PREDEFINED_OPERATOR.value
        )
