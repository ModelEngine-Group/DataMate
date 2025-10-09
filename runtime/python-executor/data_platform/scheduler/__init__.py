from .cmd_task_scheduler import CommandScheduler
from .func_task_scheduler import CallableScheduler


cmd_scheduler = CommandScheduler(max_concurrent=5)
func_scheduler = CallableScheduler(max_concurrent=5)