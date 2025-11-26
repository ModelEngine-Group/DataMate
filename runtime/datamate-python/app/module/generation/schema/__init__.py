"""QA生成模块Schema"""
from app.module.generation.schema.qa_generation import (
    CreateQATaskRequest,
    CreateQATaskResponse,
    QATaskItem,
    PagedQATaskResponse,
    QATaskDetailResponse,
    TextSplitConfig,
    QAGenerationConfig,
)

__all__ = [
    "CreateQATaskRequest",
    "CreateQATaskResponse",
    "QATaskItem",
    "PagedQATaskResponse",
    "QATaskDetailResponse",
    "TextSplitConfig",
    "QAGenerationConfig",
]
