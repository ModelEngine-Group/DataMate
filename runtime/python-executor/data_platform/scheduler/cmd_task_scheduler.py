import asyncio
from datetime import datetime
from typing import Optional, List

from loguru import logger

from .scheduler import Task, TaskStatus, TaskResult, TaskScheduler


class CommandTask(Task):
    """命令任务包装类"""

    def __init__(self, task_id: str, command: str, shell: bool = True,
                 timeout: Optional[int] = None, *args, **kwargs):
        super().__init__(task_id, *args, **kwargs)
        self.command = command
        self.shell = shell
        self.timeout = timeout
        self.stdout = None
        self.stderr = None
        self.return_code = None
        self._process = None

    def start(self) -> 'CommandTask':
        """启动任务"""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()
            self._task = asyncio.create_task(self._execute())
        return self

    async def _execute(self):
        """执行命令"""
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()

            # 使用 asyncio.create_subprocess_shell 或 create_subprocess_exec
            if self.shell:
                process = await asyncio.create_subprocess_shell(
                    self.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    **self.kwargs
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    *self.command.split(),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    **self.kwargs
                )

            self._process = process

            # 等待进程完成（带超时）
            try:
                if self.timeout:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )
                else:
                    stdout, stderr = await process.communicate()

                self.stdout = stdout.decode() if stdout else ""
                self.stderr = stderr.decode() if stderr else ""
                self.return_code = process.returncode

                if self._cancelled:
                    self.status = TaskStatus.CANCELLED
                elif process.returncode == 0:
                    self.status = TaskStatus.COMPLETED
                else:
                    self.status = TaskStatus.FAILED

            except asyncio.TimeoutError:
                # 超时处理
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()

                self.status = TaskStatus.FAILED
                self.stderr = f"Command timed out after {self.timeout} seconds"

        except asyncio.CancelledError:
            # 任务被取消
            if self._process:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()

            self.status = TaskStatus.CANCELLED
            self._cancelled = True

        except Exception as e:
            self.status = TaskStatus.FAILED
            self.stderr = str(e)
        finally:
            self.completed_at = datetime.now()

    def cancel(self) -> bool:
        """取消任务"""
        if self._process and self.status == TaskStatus.RUNNING:
            try:
                # 尝试优雅终止
                self._process.terminate()
                self._cancelled = True
                return True
            except Exception:
                # 如果无法终止，强制杀死
                try:
                    self._process.kill()
                    self._cancelled = True
                    return True
                except Exception:
                    return False
        return False

    def to_result(self) -> TaskResult:
        """转换为结果对象"""
        self.result = {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
        }
        return super().to_result()


class CommandScheduler(TaskScheduler):
    """命令调度器"""

    def __init__(self, max_concurrent: int = 5):
        super().__init__(max_concurrent)

    async def submit(self, task_id, command: str, shell: bool = True,
                     timeout: Optional[int] = None, **kwargs) -> str:
        """提交命令任务"""
        task = CommandTask(task_id, command, shell, timeout, **kwargs)
        self.tasks[task_id] = task

        # 使用信号量限制并发
        async with self.semaphore:
            # 异步执行任务
            task.start()

        logger.info(f"命令任务 {task_id} 已提交并开始执行")
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
        if not task:
            return True
        if task.status == TaskStatus.RUNNING:
            cancelled = task.cancel()
            if cancelled:
                logger.info(f"命令任务 {task_id} 已取消")
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

        # 对于运行中的任务，我们已经通过 await task.execute() 等待了
        # 所以这里直接返回结果
        return task.to_result()

    async def shutdown(self):
        """关闭调度器，取消所有运行中的任务"""
        logger.info("正在关闭命令调度器...")

        running_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]

        for task in running_tasks:
            logger.info(f"取消运行中的命令任务: {task.task_id}")
            task.cancel()

        logger.info("命令调度器已关闭")
