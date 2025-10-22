"""
通用响应模型
"""
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field

# 定义泛型类型变量
T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    """
    标准API响应格式
    
    所有API端点应返回此格式，确保响应的一致性
    """
    code: int = Field(..., description="HTTP状态码")
    message: str = Field(..., description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "message": "success",
                "data": {}
            }
        }
