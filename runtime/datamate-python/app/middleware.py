from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED
import json
import traceback
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.db.datascope import DataScopeHandle

logger = get_logger(__name__)

class UserContextMiddleware(BaseHTTPMiddleware):
    """
    读取 `User` 请求头并设置 DataScopeHandle 的 FastAPI 中间件。
    如果 `jwt_enable` 为 True，缺少请求头将返回 401。
    """

    def __init__(self, app):
        super().__init__(app)
        self.jwt_enable = settings.datamate_jwt_enable

    async def dispatch(self, request: Request, call_next):
        user: Optional[str] = request.headers.get("User")
        logger.info(f"start filter, current user: {user}, need filter: {self.jwt_enable}")
        if self.jwt_enable and (user is None or user.strip() == ""):
            payload = {"code": "common.401", "message": "unauthorized", "data": None}
            return Response(content=json.dumps(payload), status_code=HTTP_401_UNAUTHORIZED, media_type="application/json")

        DataScopeHandle.set_user_info(user)
        try:
            response = await call_next(request)
            return response
        finally:
            DataScopeHandle.remove_user_info()


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    全局异常捕获中间件

    确保所有异常都被捕获并转换为 StandardResponse 格式，
    即使在 debug 模式下也不会泄露堆栈信息给客户端。
    堆栈信息只记录到日志文件中。

    注意： BusinessException 不在此处理，由专门的异常处理器处理
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # 如果是业务异常，不要处理，让专门的异常处理器处理
            from app.core.exception import BusinessException
            if isinstance(exc, BusinessException):
                raise  # 重新抛出，由 business_exception_handler 处理

            # 记录完整的堆栈信息到日志（包含文件名、行号、完整错误）
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: {str(exc)}",
                exc_info=True  # 这会将完整堆栈记录到日志文件
            )

            # 构造安全的错误响应（不包含任何堆栈信息）
            error_response = {
                "code": "common.500",
                "message": "Internal server error",
                "data": {
                    "detail": "Internal server error"
                }
            }

            # 返回 500 状态码和统一格式的错误响应
            return Response(
                content=json.dumps(error_response),
                status_code=500,
                media_type="application/json"
            )
