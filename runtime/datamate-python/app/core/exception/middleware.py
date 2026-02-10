"""
全局异常处理中间件，支持自动响应包装

此中间件提供自动地返回值和异常转换，确保所有响应都符合标准化的 JSON 格式。
关键特性：
- 自动包装 dict/list 响应为 StandardResponse 格式
- 异常处理，并记录适当的日志
- 堆栈跟踪隔离（永远不会暴露给客户端）
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from .base import BaseError, BusinessError, SystemError
from .codes import ErrorCodes
from ..logging import get_logger

logger = get_logger(__name__)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """
    全局异常捕获中间件

    这是最外层的中间件，捕获所有未处理的异常，
    并将它们转换为标准化的响应格式。

    堆栈跟踪信息只记录到日志文件，永远不会发送给客户端。
    """

    async def dispatch(self, request: Request, call_next):
        """
        处理请求并处理任何异常

        异常会被捕获、记录（带堆栈跟踪），并转换为标准化响应。
        业务异常会被重新抛出，由专门的处理器处理。
        """
        try:
            response = await call_next(request)
            return response

        except BusinessError:
            # 让业务异常处理器处理
            raise

        except SystemError as exc:
            # 记录系统错误及其完整堆栈跟踪
            logger.error(
                f"System error occurred at {request.method} {request.url.path}",
                exc_info=True
            )
            return self._error_response(
                code=exc.code,
                message=exc.message,
                http_status=exc.http_status
            )

        except BaseError as exc:
            # 处理其他自定义错误
            logger.warning(f"BaseError occurred at {request.url.path}: {exc.message}")
            return self._error_response(
                code=exc.code,
                message=exc.message,
                http_status=exc.http_status
            )

        except Exception as exc:
            # 捕获所有未处理的异常
            logger.error(
                f"Unhandled exception occurred at {request.method} {request.url.path}",
                exc_info=True
            )
            return self._error_response(
                code=ErrorCodes.INTERNAL_ERROR.code,
                message=ErrorCodes.INTERNAL_ERROR.message,
                http_status=500
            )

    @staticmethod
    def _error_response(
        code: str,
        message: str,
        http_status: int
    ) -> StarletteResponse:
        """构建错误响应"""

        return JSONResponse(
            status_code=http_status,
            content={
                "code": code,
                "message": message,
                "data": None
            }
        )
