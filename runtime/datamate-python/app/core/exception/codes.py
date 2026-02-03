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
    SUCCESS: Final = ErrorCode("0", "操作成功", 200)
    BAD_REQUEST: Final = ErrorCode("common.0001", "请求参数错误", 400)
    NOT_FOUND: Final = ErrorCode("common.0002", "资源不存在", 404)
    FORBIDDEN: Final = ErrorCode("common.0003", "权限不足", 403)
    UNAUTHORIZED: Final = ErrorCode("common.0004", "未授权访问", 401)
    VALIDATION_ERROR: Final = ErrorCode("common.0005", "数据验证失败", 422)
    OPERATION_FAILED: Final = ErrorCode("common.0006", "操作失败", 500)

    # ========== 系统级错误码 ==========
    INTERNAL_ERROR: Final = ErrorCode("system.0001", "服务器内部错误", 500)
    DATABASE_ERROR: Final = ErrorCode("system.0002", "数据库错误", 500)
    NETWORK_ERROR: Final = ErrorCode("system.0003", "网络错误", 500)
    CONFIG_ERROR: Final = ErrorCode("system.0004", "配置错误", 500)
    SERVICE_UNAVAILABLE: Final = ErrorCode("system.0005", "服务不可用", 503)

    # ========== 标注模块 ==========
    ANNOTATION_TASK_NOT_FOUND: Final = ErrorCode("annotation.0001", "标注任务不存在", 404)
    ANNOTATION_PROJECT_NOT_FOUND: Final = ErrorCode("annotation.0002", "标注项目不存在", 404)
    ANNOTATION_TEMPLATE_NOT_FOUND: Final = ErrorCode("annotation.0003", "标注模板不存在", 404)
    ANNOTATION_FILE_NOT_FOUND: Final = ErrorCode("annotation.0004", "文件不存在", 404)
    ANNOTATION_TAG_UPDATE_FAILED: Final = ErrorCode("annotation.0005", "标签更新失败", 500)

    # ========== 归集模块 ==========
    COLLECTION_TASK_NOT_FOUND: Final = ErrorCode("collection.0001", "归集任务不存在", 404)
    COLLECTION_TEMPLATE_NOT_FOUND: Final = ErrorCode("collection.0002", "归集模板不存在", 404)
    COLLECTION_EXECUTION_NOT_FOUND: Final = ErrorCode("collection.0003", "执行记录不存在", 404)
    COLLECTION_LOG_NOT_FOUND: Final = ErrorCode("collection.0004", "日志文件不存在", 404)

    # ========== 评估模块 ==========
    EVALUATION_TASK_NOT_FOUND: Final = ErrorCode("evaluation.0001", "评估任务不存在", 404)
    EVALUATION_TASK_TYPE_ERROR: Final = ErrorCode("evaluation.0002", "任务类型错误", 400)
    EVALUATION_MODEL_NOT_FOUND: Final = ErrorCode("evaluation.0003", "评估模型不存在", 404)

    # ========== 生成模块 ==========
    GENERATION_TASK_NOT_FOUND: Final = ErrorCode("generation.0001", "合成任务不存在", 404)
    GENERATION_FILE_NOT_FOUND: Final = ErrorCode("generation.0002", "合成文件不存在", 404)
    GENERATION_CHUNK_NOT_FOUND: Final = ErrorCode("generation.0003", "数据块不存在", 404)
    GENERATION_DATA_NOT_FOUND: Final = ErrorCode("generation.0004", "合成数据不存在", 404)

    # ========== RAG 模块 ==========
    RAG_CONFIG_ERROR: Final = ErrorCode("rag.0001", "RAG配置错误", 400)
    RAG_KNOWLEDGE_BASE_NOT_FOUND: Final = ErrorCode("rag.0002", "知识库不存在", 404)
    RAG_MODEL_NOT_FOUND: Final = ErrorCode("rag.0003", "RAG模型不存在", 404)
    RAG_QUERY_FAILED: Final = ErrorCode("rag.0004", "RAG查询失败", 500)

    # ========== 比率模块 ==========
    RATIO_TASK_NOT_FOUND: Final = ErrorCode("ratio.0001", "配比任务不存在", 404)
    RATIO_NAME_REQUIRED: Final = ErrorCode("ratio.0002", "任务名称必填", 400)
    RATIO_ALREADY_EXISTS: Final = ErrorCode("ratio.0003", "任务已存在", 400)
    RATIO_DELETE_FAILED: Final = ErrorCode("ratio.0004", "删除任务失败", 500)

    # ========== 系统模块 ==========
    SYSTEM_MODEL_NOT_FOUND: Final = ErrorCode("system.0006", "模型配置不存在", 404)
    SYSTEM_MODEL_HEALTH_CHECK_FAILED: Final = ErrorCode("system.0007", "模型健康检查失败", 500)
