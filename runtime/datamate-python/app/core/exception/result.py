"""
Result 类型用于优雅的错误处理

提供受 Rust 启发的 Result<T, E> 类型，用于处理可能失败的操作而无需使用异常。

使用示例:
    # 成功情况
    def get_user(user_id: str) -> Result[User]:
        user = db.find_user(user_id)
        if user:
            return Ok(user)
        return Err(ErrorCodes.USER_NOT_FOUND)

    # 使用结果
    result = get_user("123")
    if result.is_ok():
        user = result.unwrap()
        print(f"User: {user.name}")
    else:
        error = result.unwrap_err()
        print(f"Error: {error.message}")
"""
from typing import Generic, TypeVar, Optional, Any

from .base import ErrorCode
from .codes import ErrorCodes

T = TypeVar('T')  # 成功类型
E = TypeVar('E', bound=ErrorCode)  # 错误类型


class Result(Generic[T, E]):
    """
    表示成功（Ok）或失败（Err）的 Result 类型

    此类型允许在不需要异常的情况下进行显式错误处理
    """

    def __init__(self, value: Optional[T], error: Optional[E], is_ok: bool):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @staticmethod
    def ok(value: T) -> 'Result[T, E]':
        """创建一个包含值的成功结果"""
        return Result(value, None, True)

    @staticmethod
    def err(error: E) -> 'Result[T, E]':
        """创建一个包含错误码的失败结果"""
        return Result(None, error, False)

    @property
    def is_ok(self) -> bool:
        """检查结果是否成功"""
        return self._is_ok

    @property
    def is_err(self) -> bool:
        """检查结果是否失败"""
        return not self._is_ok

    def unwrap(self) -> T:
        """
        获取成功值

        Returns:
            成功值

        Raises:
            ValueError: 如果结果是错误
        """
        if self._is_ok:
            return self._value
        raise ValueError(
            f"Cannot unwrap error result: {self._error.message}"
        )

    def unwrap_err(self) -> E:
        """
        获取错误码

        Returns:
            错误码

        Raises:
            ValueError: 如果结果是成功的
        """
        if not self._is_ok:
            return self._error
        raise ValueError("Cannot unwrap error from successful result")

    def unwrap_or(self, default: T) -> T:
        """
        获取成功值，如果出错则返回默认值

        Args:
            default: 出错时返回的默认值

        Returns:
            成功值或默认值
        """
        return self._value if self._is_ok else default

    def map(self, func) -> 'Result[Any, E]':
        """
        如果存在成功值，则应用函数

        Args:
            func: 要应用的函数

        Returns:
            包含映射值的新结果或相同的错误
        """
        if self._is_ok:
            try:
                return Result.ok(func(self._value))
            except Exception:
                # 如果映射失败，转换为错误
                return Result.err(ErrorCodes.INTERNAL_ERROR)
        return self

    def and_then(self, func) -> 'Result[Any, E]':
        """
        链式调用返回 Result 的操作

        Args:
            func: 接收成功值并返回新 Result 的函数

        Returns:
            来自函数的新结果或相同的错误
        """
        if self._is_ok:
            return func(self._value)
        return self

    def or_else(self, func) -> 'Result[T, Any]':
        """
        在出错时提供备用结果

        Args:
            func: 接收错误并返回新 Result 的函数

        Returns:
            相同的结果或来自函数的新结果
        """
        if not self._is_ok:
            return func(self._error)
        return self


def Ok(value: T) -> Result[T, ErrorCode]:
    """
    创建一个成功的结果

    使用示例:
        return Ok(user_data)
    """
    return Result.ok(value)


def Err(error_code: ErrorCode) -> Result[Any, ErrorCode]:
    """
    创建一个失败的结果

    使用示例:
        return Err(ErrorCodes.USER_NOT_FOUND)
    """
    return Result.err(error_code)
