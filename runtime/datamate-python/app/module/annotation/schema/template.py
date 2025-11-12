"""
Annotation Template Schemas
"""
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LabelDefinition(BaseModel):
    """标签定义"""
    from_name: str = Field(alias="fromName", description="控件名称")
    to_name: str = Field(alias="toName", description="目标对象名称")
    type: str = Field(description="控件类型: choices/rectanglelabels/polygonlabels/textarea/etc")
    options: Optional[List[str]] = Field(None, description="选项列表（用于choices类型）")
    labels: Optional[List[str]] = Field(None, description="标签列表（用于rectanglelabels等类型）")
    required: bool = Field(False, description="是否必填")
    description: Optional[str] = Field(None, description="标签描述")
    
    model_config = ConfigDict(populate_by_name=True)


class ObjectDefinition(BaseModel):
    """对象定义"""
    name: str = Field(description="对象标识符")
    type: str = Field(description="对象类型: Image/Text/Audio/Video/etc")
    value: str = Field(description="变量名，如$image")
    
    model_config = ConfigDict(populate_by_name=True)


class TemplateConfiguration(BaseModel):
    """模板配置结构"""
    labels: List[LabelDefinition] = Field(description="标签定义列表")
    objects: List[ObjectDefinition] = Field(description="对象定义列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")
    
    model_config = ConfigDict(populate_by_name=True)


class CreateAnnotationTemplateRequest(BaseModel):
    """创建标注模板请求"""
    name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    data_type: str = Field(alias="dataType", description="数据类型")
    labeling_type: str = Field(alias="labelingType", description="标注类型")
    configuration: TemplateConfiguration = Field(..., description="标注配置")
    style: str = Field(default="horizontal", description="样式配置")
    category: str = Field(default="custom", description="模板分类")
    
    model_config = ConfigDict(populate_by_name=True)


class UpdateAnnotationTemplateRequest(BaseModel):
    """更新标注模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    description: Optional[str] = Field(None, max_length=500, description="模板描述")
    data_type: Optional[str] = Field(None, alias="dataType", description="数据类型")
    labeling_type: Optional[str] = Field(None, alias="labelingType", description="标注类型")
    configuration: Optional[TemplateConfiguration] = Field(None, description="标注配置")
    style: Optional[str] = Field(None, description="样式配置")
    category: Optional[str] = Field(None, description="模板分类")
    
    model_config = ConfigDict(populate_by_name=True)


class AnnotationTemplateResponse(BaseModel):
    """标注模板响应"""
    id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    data_type: str = Field(alias="dataType", description="数据类型")
    labeling_type: str = Field(alias="labelingType", description="标注类型")
    configuration: TemplateConfiguration = Field(..., description="标注配置")
    label_config: Optional[str] = Field(None, alias="labelConfig", description="生成的Label Studio XML配置")
    style: str = Field(..., description="样式配置")
    category: str = Field(..., description="模板分类")
    built_in: bool = Field(alias="builtIn", description="是否内置模板")
    version: str = Field(..., description="版本号")
    created_at: datetime = Field(alias="createdAt", description="创建时间")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt", description="更新时间")
    
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AnnotationTemplateListResponse(BaseModel):
    """模板列表响应"""
    content: List[AnnotationTemplateResponse] = Field(..., description="模板列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    total_pages: int = Field(alias="totalPages", description="总页数")
    
    model_config = ConfigDict(populate_by_name=True)
