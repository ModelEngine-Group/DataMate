"""
工作协程池

使用 asyncio.Semaphore 控制并发数，替代 Java 的虚拟线程 + 信号量。
提供全局单例，确保所有文件处理共享同一个并发池。
"""
import asyncio
from typing import Callable, Any, Coroutine, Optional
import logging

logger = logging.getLogger(__name__)

# 全局单例
_global_pool: Optional["WorkerPool"] = None


def get_global_pool(max_workers: int = 10) -> "WorkerPool":
    """获取全局 WorkerPool 单例

    所有文件处理任务共享同一个并发池，确保最多 10 个文件并行处理。

    Args:
        max_workers: 最大并发数（仅在首次创建时生效）

    Returns:
        全局 WorkerPool 实例
    """
    global _global_pool
    if _global_pool is None:
        _global_pool = WorkerPool(max_workers)
        logger.info("创建全局 WorkerPool，最大并发数: %d", max_workers)
    return _global_pool


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
        self._lock = asyncio.Lock()
        self._active_count = 0

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
            async with self._lock:
                self._active_count += 1

            try:
                result = await coro(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                raise
            finally:
                async with self._lock:
                    self._active_count -= 1

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

    async def get_status(self) -> dict:
        """获取工作池状态

        Returns:
            状态字典，包含 max_workers, active_count, available
        """
        return {
            "max_workers": self.max_workers,
            "active_count": self._active_count,
            "available": self.max_workers - self._active_count,
        }
