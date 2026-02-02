from contextlib import asynccontextmanager
from typing import Dict, Any, Literal
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi_mcp import FastApiMCP
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware import UserContextMiddleware
from .core.config import settings
from .core.logging import setup_logging, get_logger
from .db.session import AsyncSessionLocal
from .exception import (
    starlette_http_exception_handler,
    fastapi_http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from .module import router
from .module.shared.schema import StandardResponse
from .module.collection.scheduler import (
    start_collection_scheduler,
    shutdown_collection_scheduler,
    load_scheduled_collection_tasks,
)

setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # @startup
    logger.info("DataMate Python Backend starting...")

    # Database connection validation
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

        def mask_db_url(url: str) -> Literal[b""] | str:
            parsed = urlparse(url)
            if parsed.password is not None:
                # 重建 netloc，将密码替换为 ****
                netloc = f"{parsed.username}:*****@{parsed.hostname}"
                if parsed.port:
                    netloc += f":{parsed.port}"
                return urlunparse(parsed._replace(netloc=netloc))
            return url

        # 使用示例
        logger.info(f"Database: {mask_db_url(settings.database_url)}")
    except Exception as e:
        logger.error(f"Database connection validation failed: {e}")
        logger.debug(f"Connection details: {settings.database_url}")
        raise

    # Label Studio
    # TODO Add actual connectivity check if needed
    logger.info(f"Label Studio: {settings.label_studio_base_url}")

    # Collection scheduler
    start_collection_scheduler()
    await load_scheduled_collection_tasks()

    yield

    # @shutdown
    shutdown_collection_scheduler()
    logger.info("DataMate Python Backend shutting down ...\n\n")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

app.add_middleware(UserContextMiddleware)
# CORS Middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.allowed_origins,
#     allow_credentials=True,
#     allow_methods=settings.allowed_methods,
#     allow_headers=settings.allowed_headers,
# )

# 注册路由
app.include_router(router)

# 输出注册的路由（每行一个）
logger.debug(f"Registered routes refer to http://localhost:{settings.port}/redoc")

# 注册全局异常处理器
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler) # type: ignore
app.add_exception_handler(HTTPException, fastapi_http_exception_handler) # type: ignore
app.add_exception_handler(RequestValidationError, validation_exception_handler) # type: ignore
app.add_exception_handler(Exception, general_exception_handler)

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
            "docs_url": "/redoc",
            "label_studio_url": settings.label_studio_base_url
        }
    )

mcp = FastApiMCP(app, name="DataMate MCP", description="DataMate python mcp server", include_tags=["mcp"])
mcp.mount_http(mount_path="/api/mcp")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
