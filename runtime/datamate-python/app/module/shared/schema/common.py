"""
通用响应模型
"""
from typing import Generic, TypeVar, Optional, List, Type
from pydantic import BaseModel, Field

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
    
    所有API端点应返回此格式，确保响应的一致性
    """
    code: int = Field(..., description="HTTP状态码")
    message: str = Field(..., description="响应消息")
    data: T = Field(..., description="响应数据")

    class Config:
        populate_by_name = True
        alias_generator = to_camel

class PaginatedData(BaseResponseModel, Generic[T]):
    """分页数据容器"""
    page: int = Field(..., description="当前页码（从1开始）")
    size: int = Field(..., description="页大小")
    total_elements: int = Field(..., description="总条数")
    total_pages: int = Field(..., description="总页数")
    content: List[T] = Field(..., description="当前页数据")
