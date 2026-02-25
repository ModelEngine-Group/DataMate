"""
工作协程池

使用 asyncio.Semaphore 控制并发数，替代 Java 的虚拟线程 + 信号量
"""
import asyncio
from typing import Callable, Any, Coroutine
import logging

logger = logging.getLogger(__name__)


class WorkerPool:
    """工作协程池

    对应 Java 的虚拟线程 + 信号量方案

    使用 asyncio.Semaphore 控制并发数，避免资源耗尽

    使用示例：
        pool = WorkerPool(max_workers=10)

        async def task_func(item):
            # 处理任务
            return result

        # 并发执行多个任务
        tasks = [pool.submit(task_func, item) for item in items]
        results = await asyncio.gather(*tasks)
    """

    def __init__(self, max_workers: int = 10):
        """初始化工作协程池

        Args:
            max_workers: 最大并发数（默认 10）
        """
        self.semaphore = asyncio.Semaphore(max_workers)
        self.max_workers = max_workers

    async def submit(
        self,
        coro: Callable[..., Coroutine],
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """提交异步任务并等待完成

        Args:
            coro: 异步协程函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            协程的返回值
        """
        async with self.semaphore:
            try:
                result = await coro(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                raise

    async def submit_batch(
        self,
        coro: Callable[..., Coroutine],
        items: list[Any],
        *args: Any,
        **kwargs: Any
    ) -> list[Any]:
        """批量提交异步任务

        Args:
            coro: 异步协程函数
            items: 要处理的项目列表
            *args: 额外的位置参数
            **kwargs: 额外的关键字参数

        Returns:
            结果列表
        """
        tasks = [
            self.submit(coro, item, *args, **kwargs)
            for item in items
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 检查是否有任务失败
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"批次任务 {i} 失败: {result}")

        return [r for r in results if not isinstance(r, Exception)]

    def get_available_workers(self) -> int:
        """获取可用的工作协程数

        Returns:
            可用的工作协程数
        """
        # 注意：Semaphore 的值在内部维护，无法直接获取
        # 这里返回最大值作为近似
        return self.max_workers
