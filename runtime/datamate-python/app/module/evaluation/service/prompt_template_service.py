"""
Service for managing evaluation prompt templates.
"""
from typing import List, Dict, Any

from app.module.evaluation.schema.prompt import EVALUATION_PROMPT_TEMPLATE
from app.module.evaluation.schema.prompt_template import (
    PromptTemplateItem,
    PromptTemplateDimension,
    PromptTemplateResponse
)


class PromptTemplateService:
    """Service for managing evaluation prompt templates"""

    @staticmethod
    def get_prompt_templates() -> PromptTemplateResponse:
        """
        Get all available prompt templates
        
        Returns:
            PromptTemplateResponse containing all prompt templates
        """
        templates = []
        
        for template in EVALUATION_PROMPT_TEMPLATE:
            # Convert dimensions to the proper schema
            dimensions = [
                PromptTemplateDimension(
                    dimension=dim.get("dimension"),
                    description=dim.get("description", "")
                )
                for dim in template.get("defaultDimensions", [])
            ]
            
            # Create template item
            template_item = PromptTemplateItem(
                evalType=template.get("evalType", ""),
                defaultDimensions=dimensions,
                prompt=template.get("prompt", "")
            )
            templates.append(template_item)
        
        return PromptTemplateResponse(templates=templates)
