"""
独立任务执行器 - 真正隔离后台任务与主事件循环

使用线程池执行CPU密集型/阻塞操作，避免阻塞主事件循环
"""
import asyncio
import concurrent.futures
from typing import Any, Callable
from functools import partial

from app.core.logging import get_logger

logger = get_logger(__name__)

# 全局线程池 - 用于执行阻塞操作
# 使用 ProcessPoolExecutor 处理CPU密集型任务，ThreadPoolExecutor 处理I/O密集型任务
_thread_pool: concurrent.futures.ThreadPoolExecutor | None = None
_process_pool: concurrent.futures.ProcessPoolExecutor | None = None

# 任务队列 - 限制并发任务数量
_task_semaphore: asyncio.Semaphore | None = None


def init_executor(
    max_workers: int = 10,
    max_concurrent_tasks: int = 5,
):
    """
    初始化执行器

    Args:
        max_workers: 线程池最大工作线程数
        max_concurrent_tasks: 最大并发任务数（同时执行的数据合成任务数）
    """
    global _thread_pool, _process_pool, _task_semaphore

    if _thread_pool is None:
        _thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="generation_task_"
        )
        logger.info(f"Initialized thread pool with {max_workers} workers")

    if _task_semaphore is None:
        _task_semaphore = asyncio.Semaphore(max_concurrent_tasks)
        logger.info(f"Initialized task semaphore with limit {max_concurrent_tasks}")


def get_thread_pool() -> concurrent.futures.ThreadPoolExecutor:
    """获取线程池，如果未初始化则自动初始化"""
    global _thread_pool
    if _thread_pool is None:
        init_executor()
    return _thread_pool


def get_task_semaphore() -> asyncio.Semaphore:
    """获取任务信号量，如果未初始化则自动初始化"""
    global _task_semaphore
    if _task_semaphore is None:
        init_executor()
    return _task_semaphore


async def run_in_thread[
    T
](func: Callable[..., T], *args, **kwargs) -> T:
    """
    在线程池中执行阻塞函数

    Args:
        func: 要执行的阻塞函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果
    """
    pool = get_thread_pool()
    loop = asyncio.get_running_loop()

    # 包装函数，添加超时和异常处理
    def wrapper():
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in thread execution: {e}")
            raise

    try:
        # 使用 asyncio.wait_for 添加超时控制
        return await asyncio.wait_for(
            loop.run_in_executor(pool, wrapper),
            timeout=300  # 5分钟超时
        )
    except asyncio.TimeoutError:
        logger.error(f"Thread execution timeout after 300s")
        raise


async def execute_generation_task(task_id: str, process_task_func: Callable[..., Any]):
    """
    执行数据合成任务，带并发控制和资源隔离

    Args:
        task_id: 任务ID
        process_task_func: 异步任务处理函数，接收task_id作为参数
    """
    semaphore = get_task_semaphore()

    async with semaphore:
        logger.info(f"Starting generation task {task_id} (semaphore acquired)")
        try:
            # 直接调用异步函数，而不是通过run_in_thread
            # 因为process_task_func已经是异步函数
            await process_task_func(task_id)
            logger.info(f"Generation task {task_id} completed successfully")
        except Exception as e:
            logger.exception(f"Generation task {task_id} failed: {e}")
            raise


def shutdown_executor():
    """关闭执行器，释放资源"""
    global _thread_pool, _process_pool, _task_semaphore

    if _thread_pool:
        _thread_pool.shutdown(wait=True)
        _thread_pool = None
        logger.info("Thread pool shutdown")

    if _process_pool:
        _process_pool.shutdown(wait=True)
        _process_pool = None
        logger.info("Process pool shutdown")

    _task_semaphore = None
