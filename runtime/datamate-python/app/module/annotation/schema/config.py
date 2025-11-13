from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.module.shared.schema import BaseResponseModel
from app.module.shared.schema import StandardResponse

class ConfigResponse(BaseResponseModel):
    """配置信息响应模型"""
    label_studio_url: str = Field(..., description="Label Studio基础URL")


class _TagAttributeConfig(BaseModel):
    """标签属性配置"""
    type: Optional[str] = Field(None, description="属性类型: boolean/string/number")
    values: Optional[List[str]] = Field(None, description="允许的枚举值列表")
    default: Optional[Any] = Field(None, description="默认值")
    description: Optional[str] = Field(None, description="属性描述")
    
    model_config = ConfigDict(populate_by_name=True)


class _TagDefinition(BaseModel):
    """标签定义"""
    description: str = Field(..., description="标签描述")
    required_attrs: List[str] = Field(default_factory=list, alias="requiredAttrs", description="必需属性列表")
    optional_attrs: Dict[str, _TagAttributeConfig] = Field(default_factory=dict, alias="optionalAttrs", description="可选属性配置")
    requires_children: bool = Field(default=False, alias="requiresChildren", description="是否需要子元素")
    child_tag: Optional[str] = Field(None, alias="childTag", description="子元素标签名")
    child_required_attrs: Optional[List[str]] = Field(None, alias="childRequiredAttrs", description="子元素必需属性")
    category: Optional[str] = Field(None, description="标签分类")
    

class TagConfigResponse(BaseResponseModel):
    """标签配置响应"""
    objects: Dict[str, _TagDefinition] = Field(default_factory=dict, description="对象标签配置")
    controls: Dict[str, _TagDefinition] = Field(default_factory=dict, description="控件标签配置")