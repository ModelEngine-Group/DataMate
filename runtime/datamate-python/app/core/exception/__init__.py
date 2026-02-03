"""
Core exception handling module.

Provides a unified, elegant exception handling system for the application.
"""

from .base import BaseError, ErrorCode, SystemError, BusinessError
from .codes import ErrorCodes
from .handlers import (
    register_exception_handlers,
    ErrorResponse,
    SuccessResponse
)
from .middleware import ExceptionHandlingMiddleware
from .result import Result, Ok, Err
from .transaction import transaction, ensure_transaction_rollback

__all__ = [
    # Base exceptions
    'BaseError',
    'ErrorCode',
    'SystemError',
    'BusinessError',
    # Error codes
    'ErrorCodes',
    # Handlers
    'register_exception_handlers',
    'ErrorResponse',
    'SuccessResponse',
    # Middleware
    'ExceptionHandlingMiddleware',
    # Result type
    'Result',
    'Ok',
    'Err',
    # Transaction management
    'transaction',
    'ensure_transaction_rollback',
]
