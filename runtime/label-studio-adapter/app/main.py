from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from typing import Dict, Any

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .infrastructure import LabelStudioClient
from .api import api_router
from .schemas import StandardResponse

# 设置日志
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    
    # 启动时初始化
    logger.info("Starting Label Studio Adapter...")
    
    # 初始化 Label Studio 客户端，使用 HTTP REST API + Token 认证
    ls_client = LabelStudioClient(
        base_url=settings.label_studio_base_url,
        token=settings.label_studio_user_token
    )
    
    logger.info("Label Studio Adapter started")
    
    yield
    
    # 关闭时清理
    logger.info("Shutting down Label Studio Adapter...")
    
    # 客户端清理会在客户端管理器中处理
    logger.info("Label Studio Adapter stopped")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# 自定义异常处理器：StarletteHTTPException (包括404等)
@app.exception_handler(StarletteHTTPException)
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
@app.exception_handler(HTTPException)
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
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将请求验证错误转换为标准响应格式"""
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "message": "error",
            "data": {
                "detail": "Validation error",
                "errors": exc.errors()
            }
        }
    )

# 自定义异常处理器：未捕获的异常
@app.exception_handler(Exception)
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

# 注册路由
app.include_router(api_router, prefix="/api")

# 测试端点：验证异常处理
@app.get("/test-404", include_in_schema=False)
async def test_404():
    """测试404异常处理"""
    raise HTTPException(status_code=404, detail="Test 404 error")

@app.get("/test-500", include_in_schema=False)
async def test_500():
    """测试500异常处理"""
    raise Exception("Test uncaught exception")

# 根路径重定向到文档
@app.get("/", response_model=StandardResponse[Dict[str, Any]], include_in_schema=False)
async def root():
    """根路径，返回服务信息"""
    return StandardResponse(
        code=200,
        message="success",
        data={
            "message": f"{settings.app_name} is running",
            "version": settings.app_version,
            "docs_url": "/docs",
            "label_studio_url": settings.label_studio_base_url
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )