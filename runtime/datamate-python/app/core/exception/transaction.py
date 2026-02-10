"""
数据库事务管理工具

提供自动事务管理的上下文管理器和依赖注入函数，
确保在异常情况下正确回滚事务。
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[None, None]:
    """
    数据库事务上下文管理器

    自动处理事务的提交和回滚：
    - 如果代码块正常执行完成，则自动提交
    - 如果代码块抛出异常，则自动回滚

    使用示例:
        @router.post("/tasks")
        async def create_task(
            request: CreateTaskRequest,
            db: AsyncSession = Depends(get_db)
        ):
            async with transaction(db):
                # 数据库操作
                db.add(task)
                await db.flush()

            # 事务已自动提交
            return SuccessResponse(data=task)

    Args:
        db: SQLAlchemy 异步会话

    Yields:
        None

    Raises:
        Exception: 重新抛出代码块中的任何异常
    """
    try:
        yield
        # 如果没有异常，提交事务
        await db.commit()
        logger.debug("Transaction committed successfully")
    except Exception as e:
        # 发生异常，回滚事务
        try:
            await db.rollback()
            logger.warning(f"Transaction rolled back due to exception: {e}")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback transaction: {rollback_error}")
        # 重新抛出异常，让上层异常处理器处理
        raise


async def ensure_transaction_rollback(db: AsyncSession) -> None:
    """
    确保事务回滚（用于错误处理）

    Args:
        db: SQLAlchemy 异步会话
    """
    try:
        await db.rollback()
        logger.debug("Transaction rolled back")
    except Exception as e:
        logger.error(f"Failed to rollback transaction: {e}")
