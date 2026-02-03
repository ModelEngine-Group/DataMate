"""
集中式错误码定义

所有错误码都在这里定义，遵循规范：{module}.{sequence}

模块代码：
- common: 通用错误
- system: 系统级错误
- annotation: 标注模块
- collection: 归集模块
- evaluation: 评估模块
- generation: 生成模块
- rag: RAG模块
- ratio: 配比模块
"""
from typing import Final

from .base import ErrorCode


class ErrorCodes:
    def __init__(self):
        self.message = None
        self.code = None

    """
    集中式错误码定义

    所有错误码在此一次性定义，使用时直接通过类属性访问。

    使用示例:
        from app.core.exception import ErrorCodes, BusinessError

        raise BusinessError(ErrorCodes.TASK_NOT_FOUND)
    """

    # ========== 通用错误码 ==========
    SUCCESS: Final = ErrorCode("0", "Success", 200)
    BAD_REQUEST: Final = ErrorCode("common.0001", "Bad request", 400)
    NOT_FOUND: Final = ErrorCode("common.0002", "Resource not found", 404)
    FORBIDDEN: Final = ErrorCode("common.0003", "Forbidden", 403)
    UNAUTHORIZED: Final = ErrorCode("common.0004", "Unauthorized", 401)
    VALIDATION_ERROR: Final = ErrorCode("common.0005", "Validation error", 422)
    OPERATION_FAILED: Final = ErrorCode("common.0006", "Operation failed", 500)

    # ========== 系统级错误码 ==========
    INTERNAL_ERROR: Final = ErrorCode("system.0001", "Internal server error", 500)
    DATABASE_ERROR: Final = ErrorCode("system.0002", "Database error", 500)
    NETWORK_ERROR: Final = ErrorCode("system.0003", "Network error", 500)
    CONFIG_ERROR: Final = ErrorCode("system.0004", "Configuration error", 500)
    SERVICE_UNAVAILABLE: Final = ErrorCode("system.0005", "Service unavailable", 503)

    # ========== 标注模块 ==========
    ANNOTATION_TASK_NOT_FOUND: Final = ErrorCode("annotation.0001", "Annotation task not found", 404)
    ANNOTATION_PROJECT_NOT_FOUND: Final = ErrorCode("annotation.0002", "Annotation project not found", 404)
    ANNOTATION_TEMPLATE_NOT_FOUND: Final = ErrorCode("annotation.0003", "Annotation template not found", 404)
    ANNOTATION_FILE_NOT_FOUND: Final = ErrorCode("annotation.0004", "File not found", 404)
    ANNOTATION_TAG_UPDATE_FAILED: Final = ErrorCode("annotation.0005", "Failed to update tags", 500)

    # ========== 归集模块 ==========
    COLLECTION_TASK_NOT_FOUND: Final = ErrorCode("collection.0001", "Collection task not found", 404)
    COLLECTION_TEMPLATE_NOT_FOUND: Final = ErrorCode("collection.0002", "Collection template not found", 404)
    COLLECTION_EXECUTION_NOT_FOUND: Final = ErrorCode("collection.0003", "Execution record not found", 404)
    COLLECTION_LOG_NOT_FOUND: Final = ErrorCode("collection.0004", "Log file not found", 404)

    # ========== 评估模块 ==========
    EVALUATION_TASK_NOT_FOUND: Final = ErrorCode("evaluation.0001", "Evaluation task not found", 404)
    EVALUATION_TASK_TYPE_ERROR: Final = ErrorCode("evaluation.0002", "Invalid task type", 400)
    EVALUATION_MODEL_NOT_FOUND: Final = ErrorCode("evaluation.0003", "Evaluation model not found", 404)

    # ========== 生成模块 ==========
    GENERATION_TASK_NOT_FOUND: Final = ErrorCode("generation.0001", "Generation task not found", 404)
    GENERATION_FILE_NOT_FOUND: Final = ErrorCode("generation.0002", "Generation file not found", 404)
    GENERATION_CHUNK_NOT_FOUND: Final = ErrorCode("generation.0003", "Data chunk not found", 404)
    GENERATION_DATA_NOT_FOUND: Final = ErrorCode("generation.0004", "Generation data not found", 404)

    # ========== RAG 模块 ==========
    RAG_CONFIG_ERROR: Final = ErrorCode("rag.0001", "RAG configuration error", 400)
    RAG_KNOWLEDGE_BASE_NOT_FOUND: Final = ErrorCode("rag.0002", "Knowledge base not found", 404)
    RAG_MODEL_NOT_FOUND: Final = ErrorCode("rag.0003", "RAG model not found", 404)
    RAG_QUERY_FAILED: Final = ErrorCode("rag.0004", "RAG query failed", 500)

    # ========== 配比模块 ==========
    RATIO_TASK_NOT_FOUND: Final = ErrorCode("ratio.0001", "Ratio task not found", 404)
    RATIO_NAME_REQUIRED: Final = ErrorCode("ratio.0002", "Task name is required", 400)
    RATIO_ALREADY_EXISTS: Final = ErrorCode("ratio.0003", "Task already exists", 400)
    RATIO_DELETE_FAILED: Final = ErrorCode("ratio.0004", "Failed to delete task", 500)

    # ========== 系统模块 ==========
    SYSTEM_MODEL_NOT_FOUND: Final = ErrorCode("system.0006", "Model configuration not found", 404)
    SYSTEM_MODEL_HEALTH_CHECK_FAILED: Final = ErrorCode("system.0007", "Model health check failed", 500)
