"""
业务异常定义

所有业务异常都应该使用 BusinessException，并使用预定义的业务错误码。
"""
from enum import Enum


class BusinessErrorCode:
    """业务错误码定义"""

    def __init__(self, message: str, error_code: str):
        """
        Args:
            message: 错误消息（会返回给客户端）
            error_code: 业务错误码（格式：{module}.{sequence}）
        """
        self.message = message
        self.error_code = error_code


class BusinessException(RuntimeError):
    """
    业务异常基类

    所有业务异常都应该抛出此异常，由全局异常处理器统一转换为 StandardResponse 格式。

    使用示例：
        # 方式1：直接使用枚举成员（推荐）
        raise BusinessException(BusinessErrorCodeEnum.TASK_NOT_FOUND)

        # 方式2：使用枚举的 value（向后兼容）
        raise BusinessException(BusinessErrorCodeEnum.TASK_NOT_FOUND.value)

    客户端将收到：
        {
            "code": "annotation.0001",
            "message": "标注任务不存在",
            "data": null
        }
    """

    def __init__(self, error_code, data=None):
        """
        Args:
            error_code: BusinessErrorCodeEnum 枚举成员（推荐）或 BusinessErrorCode 实例
            data: 附加数据（可选）
        """
        # 处理枚举成员
        from enum import Enum
        if isinstance(error_code, Enum):
            self.message = error_code.value.message
            self.error_code = error_code.value.error_code
        else:
            # 处理 BusinessErrorCode 实例
            self.message = error_code.message
            self.error_code = error_code.error_code

        self.data = data
        super().__init__(self.message)


class BusinessErrorCodeEnum(Enum):
    """
    业务错误码枚举

    错误码格式：{module}.{sequence}
    - module: 模块名（小写），如 common, annotation, collection, rag, generation, evaluation, ratio
    - sequence: 四位序号（如 0001, 0002）

    通用错误码（common）：
        - common.0001: 请求参数错误
        - common.0002: 资源不存在
        - common.0003: 权限不足
        - common.0004: 操作失败
    """

    # ========== 通用错误码 ==========
    BAD_REQUEST = BusinessErrorCode("请求参数错误", "common.0001")
    NOT_FOUND = BusinessErrorCode("资源不存在", "common.0002")
    FORBIDDEN = BusinessErrorCode("权限不足", "common.0003")
    OPERATION_FAILED = BusinessErrorCode("操作失败", "common.0004")

    # ========== System 模块 ==========
    MODEL_NOT_FOUND = BusinessErrorCode("模型配置不存在", "system.0001")
    MODEL_HEALTH_CHECK_FAILED = BusinessErrorCode("模型健康检查失败", "system.0002")

    # ========== Collection 模块 ==========
    COLLECTION_TASK_NOT_FOUND = BusinessErrorCode("归集任务不存在", "collection.0001")
    COLLECTION_TEMPLATE_NOT_FOUND = BusinessErrorCode("归集模板不存在", "collection.0002")
    COLLECTION_EXECUTION_NOT_FOUND = BusinessErrorCode("执行记录不存在", "collection.0003")
    COLLECTION_LOG_NOT_FOUND = BusinessErrorCode("日志文件不存在", "collection.0004")

    # ========== Annotation 模块 ==========
    TASK_NOT_FOUND = BusinessErrorCode("标注任务不存在", "annotation.0001")
    PROJECT_NOT_FOUND = BusinessErrorCode("标注项目不存在", "annotation.0002")
    TEMPLATE_NOT_FOUND = BusinessErrorCode("标注模板不存在", "annotation.0003")
    FILE_NOT_FOUND = BusinessErrorCode("文件不存在", "annotation.0004")
    TAG_UPDATE_FAILED = BusinessErrorCode("标签更新失败", "annotation.0005")

    # ========== Evaluation 模块 ==========
    TASK_TYPE_ERROR = BusinessErrorCode("任务类型错误", "evaluation.0001")
    EVALUATION_TASK_NOT_FOUND = BusinessErrorCode("评估任务不存在", "evaluation.0002")
    EVALUATION_MODEL_NOT_FOUND = BusinessErrorCode("评估模型不存在", "evaluation.0003")

    # ========== Generation 模块 ==========
    SYNTHESIS_TASK_NOT_FOUND = BusinessErrorCode("合成任务不存在", "generation.0001")
    SYNTHESIS_FILE_NOT_FOUND = BusinessErrorCode("合成文件不存在", "generation.0002")
    CHUNK_NOT_FOUND = BusinessErrorCode("数据块不存在", "generation.0003")
    SYNTHESIS_DATA_NOT_FOUND = BusinessErrorCode("合成数据不存在", "generation.0004")

    # ========== RAG 模块 ==========
    RAG_CONFIG_ERROR = BusinessErrorCode("RAG配置错误", "rag.0001")
    RAG_KNOWLEDGE_BASE_NOT_FOUND = BusinessErrorCode("知识库不存在", "rag.0002")
    RAG_MODEL_NOT_FOUND = BusinessErrorCode("RAG模型不存在", "rag.0003")
    RAG_QUERY_FAILED = BusinessErrorCode("RAG查询失败", "rag.0004")

    # ========== Ratio 模块 ==========
    RATIO_TASK_NOT_FOUND = BusinessErrorCode("比率任务不存在", "ratio.0001")
    RATIO_DELETE_FAILED = BusinessErrorCode("删除比率任务失败", "ratio.0002")
    RATIO_NAME_REQUIRED = BusinessErrorCode("比率任务名称必填", "ratio.0003")
    RATIO_ALREADY_EXISTS = BusinessErrorCode("比率任务已存在", "ratio.0004")
