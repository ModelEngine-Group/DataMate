"""
基础异常类和错误码定义
"""
from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorCode:
    """
    不可变的错误码定义

    属性:
        code: 错误码字符串（如 "annotation.0001"）
        message: 人类可读的错误消息
        http_status: HTTP状态码（业务错误默认为400）
    """
    code: str
    message: str
    http_status: int = 400

    def __post_init__(self):
        """验证错误码格式"""
        if not isinstance(self.code, str):
            raise ValueError(f"错误码必须是字符串，实际类型: {type(self.code)}")
        if not self.code:
            raise ValueError("错误码不能为空")


class BaseError(Exception):
    """
    所有应用异常的基类

    所有自定义异常都应该继承此类。
    提供自动的错误码和消息处理。

    使用示例:
        raise BusinessError(ErrorCodes.TASK_NOT_FOUND)

    客户端将收到:
        {
            "code": "annotation.0001",
            "message": "任务不存在",
            "data": null
        }
    """

    def __init__(
        self,
        error_code: ErrorCode,
        data: Any = None,
        *args: Any
    ):
        """
        使用错误码和可选数据初始化异常

        Args:
            error_code: ErrorCode 实例
            data: 附加错误数据（会包含在响应中）
            *args: 额外参数（用于兼容性）
        """
        self.error_code = error_code
        self.data = data
        super().__init__(error_code.message, *args)

    @property
    def code(self) -> str:
        """获取错误码字符串"""
        return self.error_code.code

    @property
    def message(self) -> str:
        """获取错误消息"""
        return self.error_code.message

    @property
    def http_status(self) -> int:
        """获取HTTP状态码"""
        return self.error_code.http_status

    def to_dict(self) -> dict:
        """将异常转换为响应字典"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class SystemError(BaseError):
    """
    系统级异常（意外错误）

    用于:
    - 数据库错误
    - 网络错误
    - 配置错误
    - 编程错误（bug）

    系统错误会记录完整的堆栈跟踪
    """

    def __init__(self, error_code: ErrorCode, data: Any = None):
        super().__init__(error_code, data)


class BusinessError(BaseError):
    """
    业务逻辑异常（预期内的错误）

    用于:
    - 验证失败
    - 资源不存在
    - 权限不足
    - 业务规则违反

    业务错误不记录堆栈跟踪（因为它们是预期的）
    """

    def __init__(self, error_code: ErrorCode, data: Any = None):
        super().__init__(error_code, data)
