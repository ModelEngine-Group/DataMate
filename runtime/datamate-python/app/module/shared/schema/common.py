"""
通用响应模型
"""
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field
from enum import Enum

# 定义泛型类型变量
T = TypeVar('T')

# 定义一个将 snake_case 转换为 camelCase 的函数
def to_camel(string: str) -> str:
    """将 snake_case 字符串转换为 camelCase"""
    components = string.split('_')
    # 首字母小写，其余单词首字母大写
    return components[0] + ''.join(x.title() for x in components[1:])

class BaseResponseModel(BaseModel):
    """基础响应模型，启用别名生成器"""

    class Config:
        populate_by_name = True
        alias_generator = to_camel

class StandardResponse(BaseResponseModel, Generic[T]):
    """
    标准API响应格式

    所有API端点（包括错误响应）都应返回此格式
    """
    code: str = Field(..., description="业务状态码（字符串）。成功使用 '0'，错误使用 '{module}.{sequence}' 格式（如 'rag.001'）")
    message: str = Field(..., description="响应消息")
    data: T = Field(default=None, description="响应数据")

    class Config:
        populate_by_name = True
        alias_generator = to_camel


class ResponseCode(str, Enum):
    """通用响应码枚举"""

    # 成功响应
    SUCCESS = "0"  # 操作成功

    # 通用错误
    BAD_REQUEST = "common.400"  # 错误的请求
    UNAUTHORIZED = "common.401"  # 未授权
    FORBIDDEN = "common.403"  # 禁止访问
    NOT_FOUND = "common.404"  # 资源未找到
    VALIDATION_ERROR = "common.422"  # 验证错误
    INTERNAL_ERROR = "common.500"  # 服务器内部错误
    SERVICE_UNAVAILABLE = "common.503"  # 服务不可用

class PaginatedData(BaseResponseModel, Generic[T]):
    """分页数据容器"""
    page: int = Field(..., description="当前页码（从1开始）")
    size: int = Field(..., description="页大小")
    total_elements: int = Field(..., description="总条数")
    total_pages: int = Field(..., description="总页数")
    content: List[T] = Field(..., description="当前页数据")

class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
