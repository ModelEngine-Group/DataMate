"""
异步任务处理模块

提供工作池和异步任务处理功能。
"""
from app.module.rag.infra.task.worker_pool import WorkerPool, get_global_pool

__all__ = ["WorkerPool", "get_global_pool"]
