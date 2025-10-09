# -*- coding: utf-8 -*-
import os

from data_platform.scheduler import cmd_scheduler


async def submit(task_id, config_path):
    current_dir = os.path.dirname(__file__)

    await cmd_scheduler.submit(task_id, f"python {os.path.join(current_dir, 'data_platform_executor.py')} "
                                        f"--config_path={config_path}")


def cancel(task_id):
    return cmd_scheduler.cancel_task(task_id)
