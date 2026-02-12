from contextlib import asynccontextmanager
from typing import Literal
from urllib.parse import urlparse, urlunparse

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from sqlalchemy import text

from app.core.config import settings
from app.core.exception import (
    register_exception_handlers,
    SuccessResponse,
    ExceptionHandlingMiddleware,
    ErrorCodes,
    BusinessError,
)
from app.core.logging import setup_logging, get_logger
from app.db.session import AsyncSessionLocal
from app.middleware import UserContextMiddleware
from app.module import router
from app.module.collection.schedule import load_scheduled_collection_tasks, set_collection_scheduler
from app.module.shared.schedule import Scheduler

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
    collection_scheduler = Scheduler(name="collection scheduler")
    collection_scheduler.start()
    set_collection_scheduler(collection_scheduler)
    await load_scheduled_collection_tasks()

    yield

    # @shutdown
    collection_scheduler.shutdown()
    logger.info("DataMate Python Backend shutting down ...\n\n")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# 注册全局异常捕获中间件（最外层，确保捕获所有异常）
# 这样即使 debug=True，也不会泄露堆栈信息给客户端
app.add_middleware(ExceptionHandlingMiddleware)

# 注册用户上下文中间件
app.add_middleware(UserContextMiddleware)

# 注册路由
app.include_router(router)

# 注册全局异常处理器
register_exception_handlers(app)

# 测试端点：验证异常处理
@app.get("/test-success", include_in_schema=False)
async def test_success():
    """测试成功响应"""
    return SuccessResponse(data={"message": "Test successful"})

@app.get("/test-business-error", include_in_schema=False)
async def test_business_error():
    """测试业务错误响应"""
    raise BusinessError(ErrorCodes.ANNOTATION_TASK_NOT_FOUND)

@app.get("/test-system-error", include_in_schema=False)
async def test_system_error():
    """测试系统错误响应"""
    raise SystemError(ErrorCodes.DATABASE_ERROR)

# 根路径
@app.get("/", include_in_schema=False)
async def root():
    """根路径，返回服务信息"""
    return SuccessResponse(
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
