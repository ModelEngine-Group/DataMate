from .cmd_task_scheduler import CommandScheduler
from .func_task_scheduler import CallableScheduler
from .job_task_scheduler import RayJobScheduler


cmd_scheduler = CommandScheduler(max_concurrent=5)
func_scheduler = CallableScheduler(max_concurrent=5)
ray_job_scheduler = RayJobScheduler(max_concurrent=5)
