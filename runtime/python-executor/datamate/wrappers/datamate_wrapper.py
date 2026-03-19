# -*- coding: utf-8 -*-
import os

from datamate.scheduler import ray_job_scheduler


async def submit(task_id, config_path):
    current_dir = os.path.dirname(__file__)
    script_path = os.path.join(current_dir, "datamate_executor.py")

    await ray_job_scheduler.submit(task_id, script_path, f"--config_path={config_path}")


def cancel(task_id):
    return ray_job_scheduler.cancel_task(task_id)
