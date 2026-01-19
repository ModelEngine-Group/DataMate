"""
Annotation Template Service
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from fastapi import HTTPException

from app.db.models.annotation_management import AnnotationTemplate
from app.module.annotation.schema.template import (
    CreateAnnotationTemplateRequest,
    UpdateAnnotationTemplateRequest,
    AnnotationTemplateResponse,
    AnnotationTemplateListResponse,
    TemplateConfiguration
)
from app.module.annotation.utils.config_validator import LabelStudioConfigValidator
from app.module.annotation.config import LabelStudioTagConfig


class AnnotationTemplateService:
    """标注模板服务"""
    
    @staticmethod
    def generate_label_studio_config(config: TemplateConfiguration) -> str:
        """
        从配置JSON生成Label Studio XML配置
        
        Args:
            config: 模板配置对象
            
        Returns:
            Label Studio XML字符串
        """
        tag_config = LabelStudioTagConfig()
        xml_parts = ['<View>']
        
        # 生成对象定义
        for obj in config.objects:
            obj_attrs = [
                f'name="{obj.name}"',
                f'value="{obj.value}"'
            ]
            xml_parts.append(f'  <{obj.type} {" ".join(obj_attrs)}/>')
        
        # 生成标签定义
        for label in config.labels:
            label_attrs = [
                f'name="{label.from_name}"',
                f'toName="{label.to_name}"'
            ]
            
            # 添加可选属性
            if label.required:
                label_attrs.append('required="true"')
            
            tag_type = label.type.capitalize() if label.type else "Choices"
            
            # 检查是否需要子元素
            if label.options or label.labels:
                choices = label.options or label.labels or []
                xml_parts.append(f'  <{tag_type} {" ".join(label_attrs)}>')
                
                # 从配置获取子元素标签名
                child_tag = tag_config.get_child_tag(tag_type)
                if not child_tag:
                    # 默认使用 Label
                    child_tag = "Label"
                
                for choice in choices:
                    xml_parts.append(f'    <{child_tag} value="{choice}"/>')
                xml_parts.append(f'  </{tag_type}>')
            else:
                # 处理简单标签类型（不需要子元素）
                xml_parts.append(f'  <{tag_type} {" ".join(label_attrs)}/>')
        
        xml_parts.append('</View>')
        return '\n'.join(xml_parts)
    
    async def create_template(
        self,
        db: AsyncSession,
        request: CreateAnnotationTemplateRequest
    ) -> AnnotationTemplateResponse:
        """
        创建标注模板
        
        Args:
            db: 数据库会话
            request: 创建请求
            
        Returns:
            创建的模板响应
        """
        # 验证配置JSON
        config_dict = request.configuration.model_dump(mode='json', by_alias=False)
        valid, error = LabelStudioConfigValidator.validate_configuration_json(config_dict)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Invalid configuration: {error}")
        
        # 生成Label Studio XML配置（用于验证，但不存储）
        label_config = self.generate_label_studio_config(request.configuration)
        
        # 验证生成的XML
        valid, error = LabelStudioConfigValidator.validate_xml(label_config)
        if not valid:
            raise HTTPException(status_code=400, detail=f"Generated XML is invalid: {error}")
        
        # 创建模板对象（不包含label_config字段）
        template = AnnotationTemplate(
            id=str(uuid4()),
            name=request.name,
            description=request.description,
            data_type=request.data_type,
            labeling_type=request.labeling_type,
            configuration=config_dict,
            style=request.style,
            category=request.category,
            built_in=False,
            version="1.0.0",
            created_at=datetime.now()
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        return self._to_response(template)
    
    async def get_template(
        self,
        db: AsyncSession,
        template_id: str
    ) -> Optional[AnnotationTemplateResponse]:
        """
        获取单个模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            模板响应或None
        """
        result = await db.execute(
            select(AnnotationTemplate)
            .where(
                AnnotationTemplate.id == template_id,
                AnnotationTemplate.deleted_at.is_(None)
            )
        )
        template = result.scalar_one_or_none()
        
        if template:
            return self._to_response(template)
        return None
    
    async def list_templates(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        category: Optional[str] = None,
        data_type: Optional[str] = None,
        labeling_type: Optional[str] = None,
        built_in: Optional[bool] = None
    ) -> AnnotationTemplateListResponse:
        """
        获取模板列表
        
        Args:
            db: 数据库会话
            page: 页码
            size: 每页大小
            category: 分类筛选
            data_type: 数据类型筛选
            labeling_type: 标注类型筛选
            built_in: 是否内置模板筛选
            
        Returns:
            模板列表响应
        """
        # 构建查询条件
        conditions: List = [AnnotationTemplate.deleted_at.is_(None)]
        
        if category:
            conditions.append(AnnotationTemplate.category == category)  # type: ignore
        if data_type:
            conditions.append(AnnotationTemplate.data_type == data_type)  # type: ignore
        if labeling_type:
            conditions.append(AnnotationTemplate.labeling_type == labeling_type)  # type: ignore
        if built_in is not None:
            conditions.append(AnnotationTemplate.built_in == built_in)  # type: ignore
        
        # 查询总数
        count_result = await db.execute(
            select(func.count()).select_from(AnnotationTemplate).where(*conditions)
        )
        total = count_result.scalar() or 0
        
        # 分页查询
        result = await db.execute(
            select(AnnotationTemplate)
            .where(*conditions)
            .order_by(AnnotationTemplate.created_at.desc())
            .limit(size)
            .offset((page - 1) * size)
        )
        templates = result.scalars().all()
        
        return AnnotationTemplateListResponse(
            content=[self._to_response(t) for t in templates],
            totalElements=total,
            page=page,
            size=size,
            totalPages=(total + size - 1) // size
        )
    
    async def update_template(
        self,
        db: AsyncSession,
        template_id: str,
        request: UpdateAnnotationTemplateRequest
    ) -> Optional[AnnotationTemplateResponse]:
        """
        更新模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            request: 更新请求
            
        Returns:
            更新后的模板响应或None
        """
        result = await db.execute(
            select(AnnotationTemplate)
            .where(
                AnnotationTemplate.id == template_id,
                AnnotationTemplate.deleted_at.is_(None)
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return None
        
        # 更新字段
        update_data = request.model_dump(exclude_unset=True, by_alias=False)
        
        for field, value in update_data.items():
            if field == 'configuration' and value is not None:
                # 验证配置JSON
                config_dict = value.model_dump(mode='json', by_alias=False)
                valid, error = LabelStudioConfigValidator.validate_configuration_json(config_dict)
                if not valid:
                    raise HTTPException(status_code=400, detail=f"Invalid configuration: {error}")
                
                # 重新生成Label Studio XML配置（用于验证）
                label_config = self.generate_label_studio_config(value)
                
                # 验证生成的XML
                valid, error = LabelStudioConfigValidator.validate_xml(label_config)
                if not valid:
                    raise HTTPException(status_code=400, detail=f"Generated XML is invalid: {error}")
                
                # 只更新configuration字段，不存储label_config
                setattr(template, field, config_dict)
            else:
                setattr(template, field, value)
        
        template.updated_at = datetime.now()  # type: ignore
        
        await db.commit()
        await db.refresh(template)
        
        return self._to_response(template)
    
    async def delete_template(
        self,
        db: AsyncSession,
        template_id: str
    ) -> bool:
        """
        删除模板（软删除）
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            是否删除成功
        """
        result = await db.execute(
            select(AnnotationTemplate)
            .where(
                AnnotationTemplate.id == template_id,
                AnnotationTemplate.deleted_at.is_(None)
            )
        )
        template = result.scalar_one_or_none()
        
        if not template:
            return False
        
        template.deleted_at = datetime.now()  # type: ignore
        await db.commit()
        
        return True
    
    def _to_response(self, template: AnnotationTemplate) -> AnnotationTemplateResponse:
        """
        转换为响应对象
        
        Args:
            template: 数据库模型对象
            
        Returns:
            模板响应对象
        """
        # 将配置JSON转换为TemplateConfiguration对象
        from typing import cast, Dict, Any
        config_dict = cast(Dict[str, Any], template.configuration)
        config = TemplateConfiguration(**config_dict)
        
        # 动态生成Label Studio XML配置
        label_config = self.generate_label_studio_config(config)
        
        # 使用model_validate从ORM对象创建响应对象
        response = AnnotationTemplateResponse.model_validate(template)
        response.configuration = config
        response.label_config = label_config  # type: ignore
        
        return response
