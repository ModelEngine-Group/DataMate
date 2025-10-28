from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from app.core.logging import get_logger
from typing import AsyncGenerator

logger = get_logger(__name__)

# 获取数据库配置信息
db_info = settings.get_database_info()
logger.info(f"使用数据库: {db_info['type']}")
logger.info(f"连接URL: {db_info['url']}")

# 创建数据库引擎
engine = create_async_engine(
    settings.computed_database_url,
    echo=False,  # 关闭SQL调试日志以减少输出
    future=True,
    # SQLite特殊配置
    connect_args={"check_same_thread": False} if "sqlite" in settings.computed_database_url else {}
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 创建基础模型类
Base = declarative_base()
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            