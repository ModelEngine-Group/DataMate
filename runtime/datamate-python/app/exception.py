"""
全局自定义异常类定义
"""
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, HTTPException, status

from .core.logging import setup_logging, get_logger

logger = get_logger(__name__)

# 自定义异常处理器：StarletteHTTPException (包括404等)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """将Starlette的HTTPException转换为标准响应格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": "error",
            "data": {
                "detail": exc.detail
            }
        }
    )

# 自定义异常处理器：FastAPI HTTPException
async def fastapi_http_exception_handler(request: Request, exc: HTTPException):
    """将FastAPI的HTTPException转换为标准响应格式"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": "error",
            "data": {
                "detail": exc.detail
            }
        }
    )

# 自定义异常处理器：RequestValidationError
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将请求验证错误转换为标准响应格式"""
    # 仅返回每个错误的简要 detail 文本（来自 Pydantic 错误的 `msg` 字段），不返回整个错误对象
    raw_errors = exc.errors() or []
    errors = [err.get("msg", "Validation error") for err in raw_errors]

    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "error",
            "data": {
                "detail": "Validation error",
                "errors": errors,
            },
        },
    )

# 自定义异常处理器：未捕获的异常
async def general_exception_handler(request: Request, exc: Exception):
    """将未捕获的异常转换为标准响应格式"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "error",
            "data": {
                "detail": "Internal server error"
            }
        }
    )

class LabelStudioAdapterException(Exception):
    """Label Studio Adapter 基础异常类"""
    pass

class DatasetMappingNotFoundError(LabelStudioAdapterException):
    """数据集映射未找到异常"""
    def __init__(self, mapping_id: str):
        self.mapping_id = mapping_id
        super().__init__(f"Dataset mapping not found: {mapping_id}")

class NoDatasetInfoFoundError(LabelStudioAdapterException):
    """无法获取数据集信息异常"""
    def __init__(self, dataset_uuid: str):
        self.dataset_uuid = dataset_uuid
        super().__init__(f"Failed to get dataset info: {dataset_uuid}")

class LabelStudioClientError(LabelStudioAdapterException):
    """Label Studio 客户端错误"""
    pass

class DMServiceClientError(LabelStudioAdapterException):
    """DM 服务客户端错误"""
    pass

class SyncServiceError(LabelStudioAdapterException):
    """同步服务错误"""
    pass
