import asyncio
from datetime import datetime
from typing import Callable, Optional, List

from loguru import logger

from .scheduler import TaskStatus, TaskResult, Task, TaskScheduler


class CallableTask(Task):
    """任务包装类"""

    def __init__(self, task_id: str, func: Callable, *args, **kwargs):
        super().__init__(task_id, *args, **kwargs)
        self.func = func

    def start(self) -> 'CallableTask':
        """启动任务"""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()
            self._task = asyncio.create_task(self._execute())
        return self

    async def _execute(self):
        """执行任务"""
        try:
            self.result = await self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
        except asyncio.CancelledError:
            self.status = TaskStatus.CANCELLED
            self._cancelled = True
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
        finally:
            self.completed_at = datetime.now()

    def cancel(self) -> bool:
        """取消任务"""
        if self._task and not self._task.done():
            self._task.cancel()
            return True
        return False


class CallableScheduler(TaskScheduler):
    """异步任务调度器"""

    def __init__(self, max_concurrent: int = 10):
        super().__init__(max_concurrent)

    async def submit(self, task_id, func: Callable, *args, **kwargs) -> str:
        """提交任务"""
        task = CallableTask(task_id, func, *args, **kwargs)
        self.tasks[task_id] = task

        # 使用信号量限制并发
        async with self.semaphore:
            task.start()

        logger.info(f"任务 {task_id} 已提交并开始执行")
        return task_id

    def get_task_status(self, task_id: str) -> Optional[TaskResult]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return task.to_result()
        return None

    def get_all_tasks(self) -> List[TaskResult]:
        """获取所有任务状态"""
        return [task.to_result() for task in self.tasks.values()]

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.RUNNING:
            cancelled = task.cancel()
            if cancelled:
                logger.info(f"任务 {task_id} 已取消")
            return cancelled
        return False

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskResult]:
        """根据状态获取任务"""
        return [
            task.to_result()
            for task in self.tasks.values()
            if task.status == status
        ]

    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """等待任务完成"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return task.to_result()

        # 等待任务完成
        if task.get():
            try:
                await asyncio.wait_for(task.get(), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"任务 {task_id} 超时")

        return task.to_result()

    async def shutdown(self):
        """关闭调度器，取消所有运行中的任务"""
        logger.info("正在关闭调度器...")

        running_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]

        for task in running_tasks:
            logger.info(f"取消运行中的任务: {task.task_id}")
            task.cancel()

        # 等待所有任务完成
        for task in running_tasks:
            if task.get() and not task.get().done():
                try:
                    await asyncio.wait_for(task.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"任务 {task.task_id} 无法正常停止")

        logger.info("调度器已关闭")
