# -*- coding: utf-8 -*-
import os

from datamate.common.utils import is_k8s
from datamate.scheduler import cmd_scheduler
from datamate.scheduler import ray_job_scheduler


async def submit(task_id, config_path, retry_count: int = 0):
    current_dir = os.path.dirname(__file__)

    if not is_k8s():
        await cmd_scheduler.submit(task_id, f"python {os.path.join(current_dir, 'datamate_executor.py')} "
                                            f"--config_path={config_path}")
        return

    script_path = os.path.join(current_dir, "datamate_executor.py")

    # 根据 retry_count 设置日志路径
    if retry_count > 0:
        log_path = f"/flow/{task_id}/output.log.{retry_count}"
    else:
        log_path = f"/flow/{task_id}/output.log"

    await ray_job_scheduler.submit(
        task_id, script_path, f"--config_path={config_path}", log_path=log_path
    )


def cancel(task_id):
    if not is_k8s():
        return cmd_scheduler.cancel_task(task_id)
    return ray_job_scheduler.cancel_task(task_id)
