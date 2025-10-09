# 任务状态枚举
import asyncio
import signal
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Dict, List
from loguru import logger


class TaskStatus(Enum):
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在运行
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class TaskResult:
    """任务结果数据类"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0


class Task:
    def __init__(self, task_id: str, *args, **kwargs):
        self.task_id = task_id
        self.args = args
        self.kwargs = kwargs
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.progress = 0.0
        self._task = None  # asyncio.Task 实例
        self._cancelled = False

    def get(self):
        return self._task

    def start(self) -> 'Task':
        """启动任务"""
        pass

    async def _execute(self):
        """执行任务"""
        pass

    def cancel(self) -> bool:
        """取消任务"""
        pass

    def to_result(self) -> TaskResult:
        """转换为结果对象"""
        return TaskResult(
            task_id=self.task_id,
            status=self.status,
            result=self.result,
            error=self.error,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            progress=self.progress
        )


class TaskScheduler:
    """异步任务调度器"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, Task] = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 注册信号处理器
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (ValueError, AttributeError):
            # 在某些平台上可能不支持
            pass

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在清理任务...")
        asyncio.create_task(self.shutdown())
        sys.exit(0)

    async def submit(self, task_id, task, *args, **kwargs) -> str:
        """提交任务"""
        pass

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
        pass

    async def shutdown(self):
        """关闭调度器，取消所有运行中的任务"""
        pass

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = {
            TaskStatus.PENDING: 0,
            TaskStatus.RUNNING: 0,
            TaskStatus.COMPLETED: 0,
            TaskStatus.FAILED: 0,
            TaskStatus.CANCELLED: 0
        }

        for task in self.tasks.values():
            stats[task.status] += 1

        return {
            "pending": stats[TaskStatus.PENDING],
            "running": stats[TaskStatus.RUNNING],
            "completed": stats[TaskStatus.COMPLETED],
            "failed": stats[TaskStatus.FAILED],
            "cancelled": stats[TaskStatus.CANCELLED],
            "total": len(self.tasks)
        }
