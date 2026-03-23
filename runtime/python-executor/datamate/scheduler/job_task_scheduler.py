import asyncio
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from loguru import logger

from .scheduler import Task, TaskStatus, TaskResult, TaskScheduler

# Default Ray dashboard address
RAY_DASHBOARD_ADDRESS = os.getenv("RAY_DASHBOARD_ADDRESS", "http://datamate-raycluster-head-svc:8265")


class RayJobTask(Task):
    """Ray Job 任务包装类"""

    def __init__(
        self,
        task_id: str,
        entrypoint: str,
        runtime_env: Optional[Dict[str, Any]] = None,
        log_path: Optional[str] = None,
        timeout: Optional[int] = None,
        *args,
        **kwargs,
    ):
        super().__init__(task_id, *args, **kwargs)
        self.entrypoint = entrypoint
        self.runtime_env = runtime_env or {}
        self.log_path = log_path or f"/flow/{task_id}/output.log"
        self.timeout = timeout
        self.job_id: Optional[str] = None
        self._client = None

    def _get_client(self):
        """延迟初始化 JobSubmissionClient"""
        if self._client is None:
            from ray.job_submission import JobSubmissionClient

            self._client = JobSubmissionClient(RAY_DASHBOARD_ADDRESS)
        return self._client

    def start(self) -> "RayJobTask":
        """启动任务"""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()
            self._task = asyncio.create_task(self._execute())
        return self

    async def _execute(self):
        """执行 Ray Job"""
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.now()

            client = self._get_client()

            # 确保 log 目录存在
            log_dir = os.path.dirname(self.log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # 提交 Ray Job
            self.job_id = client.submit_job(
                entrypoint=self.entrypoint,
                runtime_env=self.runtime_env,
                metadata={"task_id": self.task_id},
            )
            logger.info(f"Submitted Ray Job: {self.job_id} for task {self.task_id}")

            # 轮询 Job 状态
            poll_interval = 2  # 2 秒轮询一次
            elapsed_time = 0
            last_log_position = 0  # 记录已写入的日志位置

            while True:
                if self._cancelled:
                    logger.info(
                        f"Task {self.task_id} cancelled, stopping Ray Job {self.job_id}"
                    )
                    self._stop_job(client)
                    self.status = TaskStatus.CANCELLED
                    break

                try:
                    info = client.get_job_info(self.job_id)
                    job_status = info.status

                    # 获取并写入日志
                    await self._fetch_and_write_logs(client, last_log_position)
                    last_log_position = os.path.getsize(self.log_path) if os.path.exists(self.log_path) else 0

                    if job_status == "SUCCEEDED":
                        self.status = TaskStatus.COMPLETED
                        logger.info(f"Ray Job {self.job_id} completed successfully")
                        break
                    elif job_status == "FAILED":
                        self.status = TaskStatus.FAILED
                        self.error = info.message or "Job failed"
                        logger.error(f"Ray Job {self.job_id} failed: {self.error}")
                        break
                    elif job_status == "STOPPED":
                        if self._cancelled:
                            self.status = TaskStatus.CANCELLED
                        else:
                            self.status = TaskStatus.FAILED
                            self.error = "Job was stopped unexpectedly"
                        logger.info(f"Ray Job {self.job_id} stopped")
                        break

                    # 检查超时
                    if self.timeout and elapsed_time >= self.timeout:
                        logger.warning(
                            f"Ray Job {self.job_id} timed out after {self.timeout} seconds"
                        )
                        self._stop_job(client)
                        self.status = TaskStatus.FAILED
                        self.error = f"Job timed out after {self.timeout} seconds"
                        break

                except Exception as e:
                    logger.warning(f"Error checking job status: {e}")

                await asyncio.sleep(poll_interval)
                elapsed_time += poll_interval

        except asyncio.CancelledError:
            logger.info(f"Task {self.task_id} received CancelledError")
            if self.job_id:
                client = self._get_client()
                self._stop_job(client)
            self.status = TaskStatus.CANCELLED
            self._cancelled = True

        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            logger.error(f"RayJobTask(id: {self.task_id}) run failed. Cause: {e}")

        finally:
            self.completed_at = datetime.now()

    async def _fetch_and_write_logs(self, client, last_position: int = 0):
        """获取 Ray Job 日志并追加写入日志文件"""
        try:
            logs = client.get_job_logs(self.job_id)
            if logs:
                log_content = logs if isinstance(logs, str) else str(logs)
                # 只追加新日志
                if len(log_content) > last_position:
                    new_logs = log_content[last_position:]
                    with open(self.log_path, "a", encoding="utf-8") as f:
                        f.write(new_logs)
                        if not new_logs.endswith("\n"):
                            f.write("\n")
        except Exception as e:
            logger.warning(f"Failed to fetch logs for job {self.job_id}: {e}")

    def _stop_job(self, client):
        """停止 Ray Job"""
        if self.job_id:
            try:
                client.stop_job(self.job_id)
                logger.info(f"Stopped Ray Job {self.job_id}")
            except Exception as e:
                logger.warning(f"Failed to stop Ray Job {self.job_id}: {e}")

    def cancel(self) -> bool:
        """取消任务"""
        if self.status == TaskStatus.RUNNING:
            self._cancelled = True
            logger.info(f"Marked Ray Job task {self.task_id} for cancellation")
            return True
        return False

    def to_result(self) -> TaskResult:
        """转换为结果对象"""
        self.result = {
            "entrypoint": self.entrypoint,
            "job_id": self.job_id,
        }
        return super().to_result()


class RayJobScheduler(TaskScheduler):
    """Ray Job 调度器"""

    def __init__(self, max_concurrent: int = 5, ray_address: Optional[str] = None):
        super().__init__(max_concurrent)
        self.ray_address = ray_address or RAY_DASHBOARD_ADDRESS
        self._client = None

    def _get_client(self):
        """延迟初始化 JobSubmissionClient"""
        if self._client is None:
            from ray.job_submission import JobSubmissionClient

            self._client = JobSubmissionClient(self.ray_address)
        return self._client

    async def submit(
        self,
        task_id: str,
        script_path: str,
        script_args: str = "",
        runtime_env: Optional[Dict[str, Any]] = None,
        log_path: Optional[str] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> str:
        """提交 Ray Job 任务"""
        # 构建 entrypoint
        entrypoint = f"python {script_path}"
        if script_args:
            entrypoint = f"{entrypoint} {script_args}"

        # 默认 runtime_env
        if runtime_env is None:
            runtime_env = {"working_dir": "/opt/runtime"}

        # 默认 log_path
        if log_path is None:
            log_path = f"/flow/{task_id}/output.log"

        task = RayJobTask(
            task_id=task_id,
            entrypoint=entrypoint,
            runtime_env=runtime_env,
            log_path=log_path,
            timeout=timeout,
            **kwargs,
        )
        self.tasks[task_id] = task

        # 使用信号量限制并发
        async with self.semaphore:
            task.start()

        logger.info(f"Ray Job 任务 {task_id} 已提交并开始执行")
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
            logger.warning(f"Task {task_id} not found, considering already cancelled")
            return True

        if task.status == TaskStatus.RUNNING:
            cancelled = task.cancel()
            if cancelled:
                logger.info(f"Ray Job 任务 {task_id} 已标记为取消")
            return cancelled

        # 任务未运行，直接返回成功
        if task.status in [TaskStatus.PENDING, TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return True

        return False

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskResult]:
        """根据状态获取任务"""
        return [
            task.to_result() for task in self.tasks.values() if task.status == status
        ]

    async def wait_for_task(
        self, task_id: str, timeout: Optional[float] = None
    ) -> TaskResult:
        """等待任务完成"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"任务 {task_id} 不存在")

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return task.to_result()

        # 等待任务完成
        if task.get():
            try:
                await asyncio.wait_for(task.get(), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"任务 {task_id} 等待超时")

        return task.to_result()

    async def shutdown(self):
        """关闭调度器，取消所有运行中的任务"""
        logger.info("正在关闭 Ray Job 调度器...")

        running_tasks = [
            task for task in self.tasks.values() if task.status == TaskStatus.RUNNING
        ]

        for task in running_tasks:
            logger.info(f"取消运行中的 Ray Job 任务: {task.task_id}")
            task.cancel()

        # 等待所有任务完成
        for task in running_tasks:
            if task.get() and not task.get().done():
                try:
                    await asyncio.wait_for(task.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"任务 {task.task_id} 无法正常停止")

        logger.info("Ray Job 调度器已关闭")
