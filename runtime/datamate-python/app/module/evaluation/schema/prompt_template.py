"""
Schema for evaluation prompt templates.
"""
from typing import List
from pydantic import BaseModel, Field


class PromptTemplateDimension(BaseModel):
    """A single dimension in the prompt template"""
    dimension: str = Field(..., description="Dimension name")
    description: str = Field(..., description="Description of the dimension")


class PromptTemplateItem(BaseModel):
    """A single prompt template item"""
    evalType: str = Field(..., description="Evaluation type")
    defaultDimensions: List[PromptTemplateDimension] = Field(
        default_factory=list,
        description="List of default dimensions for this evaluation type"
    )
    prompt: str = Field(..., description="The prompt template string")


class PromptTemplateResponse(BaseModel):
    """Response model for getting prompt templates"""
    templates: List[PromptTemplateItem] = Field(
        ...,
        description="List of available prompt templates"
    )
