"""
异常处理器和响应构建器

提供异常的自动转换，将异常转换为标准化的 JSON 响应。
"""
from typing import Any, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .base import BaseError, BusinessError, SystemError
from .codes import ErrorCodes
from ..logging import get_logger

logger = get_logger(__name__)


def SuccessResponse(data: Any = None, message: str = "success", code: str = "0") -> dict:
    """
    构建成功响应

    Args:
        data: 响应数据
        message: 成功消息
        code: 自定义成功码（默认为 "0"）

    Returns:
        响应字典，符合 StandardResponse 格式

    使用示例:
        return SuccessResponse(data={"id": 123})
        # 或
        return SuccessResponse({"id": 123})
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def ErrorResponse(
    error_code: ErrorCodes,
    data: Any = None,
    custom_message: Optional[str] = None
) -> dict:
    """
    构建错误响应

    Args:
        error_code: 错误码（来自 ErrorCodes）
        data: 附加错误数据
        custom_message: 覆盖默认错误消息

    Returns:
        响应字典，符合 StandardResponse 格式

    使用示例:
        return ErrorResponse(ErrorCodes.TASK_NOT_FOUND)
    """
    return {
        "code": error_code.code,
        "message": custom_message or error_code.message,
        "data": data
    }


async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    """
    处理业务逻辑异常

    业务异常是预期的错误，不需要记录堆栈跟踪。
    返回对应的 HTTP 状态码（400、404 等），错误信息在响应体的 code 字段中。
    """
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_dict()
    )


async def system_error_handler(request: Request, exc: SystemError) -> JSONResponse:
    """
    处理系统异常

    系统异常是意外的错误，需要记录完整的堆栈跟踪。
    返回 HTTP 500 和经过净化的错误消息。
    """
    logger.error(
        f"System error occurred at {request.method} {request.url.path}: {exc.message}",
        exc_info=True
    )

    return JSONResponse(
        status_code=exc.http_status,
        content={
            "code": exc.code,
            "message": exc.message,
            "data": None  # 绝不暴露系统错误详情
        }
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """处理请求验证错误"""
    errors = exc.errors()
    simplified_errors = [
        err.get("msg", "Validation error")
        for err in errors
    ]

    return JSONResponse(
        status_code=422,
        content={
            "code": ErrorCodes.VALIDATION_ERROR.code,
            "message": ErrorCodes.VALIDATION_ERROR.message,
            "data": {
                "detail": "请求验证失败",
                "errors": simplified_errors
            }
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """处理 HTTP 异常（404、500 等）"""
    # 根据 HTTP 状态码映射到错误码
    error_code = ErrorCodes.INTERNAL_ERROR
    if exc.status_code == 404:
        error_code = ErrorCodes.NOT_FOUND
    elif exc.status_code == 401:
        error_code = ErrorCodes.UNAUTHORIZED
    elif exc.status_code == 403:
        error_code = ErrorCodes.FORBIDDEN
    elif exc.status_code == 422:
        error_code = ErrorCodes.VALIDATION_ERROR
    elif exc.status_code == 400:
        error_code = ErrorCodes.BAD_REQUEST

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": error_code.code,
            "message": "error",
            "data": {
                "detail": str(exc.detail)
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    通用异常处理器（最后的兜底处理）

    这是最后一道防线 - 记录完整的堆栈跟踪
    并返回经过净化的错误给客户端。
    """
    logger.error(
        f"Unhandled exception occurred at {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCodes.INTERNAL_ERROR.code,
            "message": ErrorCodes.INTERNAL_ERROR.message,
            "data": {
                "detail": "服务器内部错误"
            }
        }
    )


def register_exception_handlers(app) -> None:
    """
    注册所有异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例

    使用示例:
        from app.core.exception import register_exception_handlers

        app = FastAPI()
        register_exception_handlers(app)
    """
    from .base import BusinessError, SystemError

    # 按照特异性顺序注册异常处理器（最具体的在前）
    app.add_exception_handler(BusinessError, business_error_handler)
    app.add_exception_handler(SystemError, system_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
