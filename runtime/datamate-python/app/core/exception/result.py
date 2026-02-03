"""
Result type for elegant error handling.

Provides a Rust-inspired Result<T, E> type for handling operations
that can fail without exceptions.

Usage:
    # Success case
    def get_user(user_id: str) -> Result[User]:
        user = db.find_user(user_id)
        if user:
            return Ok(user)
        return Err(ErrorCodes.USER_NOT_FOUND)

    # Using the result
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

T = TypeVar('T')  # Success type
E = TypeVar('E', bound=ErrorCode)  # Error type


class Result(Generic[T, E]):
    """
    Result type representing either success (Ok) or failure (Err).

    This type allows explicit error handling without exceptions.
    """

    def __init__(self, value: Optional[T], error: Optional[E], is_ok: bool):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @staticmethod
    def ok(value: T) -> 'Result[T, E]':
        """Create a successful result containing a value."""
        return Result(value, None, True)

    @staticmethod
    def err(error: E) -> 'Result[T, E]':
        """Create a failed result containing an error code."""
        return Result(None, error, False)

    @property
    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self._is_ok

    @property
    def is_err(self) -> bool:
        """Check if result is failed."""
        return not self._is_ok

    def unwrap(self) -> T:
        """
        Get the success value.

        Returns:
            The success value

        Raises:
            ValueError: If result is an error
        """
        if self._is_ok:
            return self._value
        raise ValueError(
            f"Cannot unwrap error result: {self._error.message}"
        )

    def unwrap_err(self) -> E:
        """
        Get the error code.

        Returns:
            The error code

        Raises:
            ValueError: If result is successful
        """
        if not self._is_ok:
            return self._error
        raise ValueError("Cannot unwrap error from successful result")

    def unwrap_or(self, default: T) -> T:
        """
        Get success value or default if error.

        Args:
            default: Default value to return on error

        Returns:
            Success value or default
        """
        return self._value if self._is_ok else default

    def map(self, func) -> 'Result[Any, E]':
        """
        Apply function to success value if present.

        Args:
            func: Function to apply

        Returns:
            New result with mapped value or same error
        """
        if self._is_ok:
            try:
                return Result.ok(func(self._value))
            except Exception as exc:
                # If mapping fails, convert to error
                return Result.err(ErrorCodes.INTERNAL_ERROR)
        return self

    def and_then(self, func) -> 'Result[Any, E]':
        """
        Chain operations that return Results.

        Args:
            func: Function that takes success value and returns new Result

        Returns:
            New result from function or same error
        """
        if self._is_ok:
            return func(self._value)
        return self

    def or_else(self, func) -> 'Result[T, Any]':
        """
        Provide fallback result on error.

        Args:
            func: Function that takes error and returns new Result

        Returns:
            Same result or new result from function
        """
        if not self._is_ok:
            return func(self._error)
        return self


def Ok(value: T) -> Result[T, ErrorCode]:
    """
    Create a successful result.

    Usage:
        return Ok(user_data)
    """
    return Result.ok(value)


def Err(error_code: ErrorCode) -> Result[Any, ErrorCode]:
    """
    Create a failed result.

    Usage:
        return Err(ErrorCodes.USER_NOT_FOUND)
    """
    return Result.err(error_code)
