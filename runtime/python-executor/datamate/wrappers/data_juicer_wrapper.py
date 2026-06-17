# -*- coding: utf-8 -*-
import os

from datamate.scheduler import cmd_scheduler


async def submit(task_id, config_path):
    current_dir = os.path.dirname(__file__)
    executor_script = os.path.join(current_dir, 'data_juicer_executor.py')

    # Use argument list to avoid shell injection (CodeQL / FCE)
    await cmd_scheduler.submit(
        task_id,
        cmd_args=["python", executor_script, f"--config_path={config_path}"]
    )

def cancel(task_id):
    return cmd_scheduler.cancel_task(task_id)
