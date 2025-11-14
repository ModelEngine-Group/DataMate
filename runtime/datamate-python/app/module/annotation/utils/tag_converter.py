"""
Tag Format Converter

Converts simplified external tag format to internal storage format by looking up
the type from the annotation template configuration.

External format (from users):
[
    {
        "from_name": "label",
        "to_name": "image",
        "values": ["cat", "dog"]
    }
]

Internal storage format:
[
    {
        "id": "unique_id",
        "from_name": "label",
        "to_name": "image", 
        "type": "choices",
        "value": {
            "choices": ["cat", "dog"]
        }
    }
]
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logging import get_logger
from ..schema.template import TemplateConfiguration

logger = get_logger(__name__)


class TagFormatConverter:
    """Convert between simplified external tag format and internal storage format"""
    
    def __init__(self, template_config: TemplateConfiguration):
        """
        Initialize converter with template configuration
        
        Args:
            template_config: The template configuration containing label definitions
        """
        self.template_config = template_config
        # Build a lookup map: from_name -> type
        self._type_map = self._build_type_map()
        
    def _build_type_map(self) -> Dict[str, str]:
        """
        Build a mapping from from_name to type from template labels
        
        Returns:
            Dictionary mapping from_name to control type
        """
        type_map = {}
        for label_def in self.template_config.labels:
            from_name = label_def.from_name
            control_type = label_def.type
            type_map[from_name] = control_type
            logger.debug(f"Registered control: {from_name} -> {control_type}")
        
        return type_map
    
    def get_type_for_from_name(self, from_name: str) -> Optional[str]:
        """
        Get the control type for a given from_name
        
        Args:
            from_name: The control name
            
        Returns:
            Control type or None if not found
        """
        return self._type_map.get(from_name)
    
    def convert_simplified_to_full(
        self, 
        simplified_tags: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert simplified tag format to full internal storage format
        
        Args:
            simplified_tags: List of tags in simplified format with structure:
                [
                    {
                        "from_name": "label",
                        "to_name": "image",
                        "values": ["cat", "dog"]  # Can be list or single value
                    }
                ]
        
        Returns:
            List of tags in full internal format:
                [
                    {
                        "id": "unique_id",
                        "from_name": "label",
                        "to_name": "image",
                        "type": "choices",
                        "value": {
                            "choices": ["cat", "dog"]
                        }
                    }
                ]
        """
        full_tags = []
        
        for simplified_tag in simplified_tags:
            # Support both camelCase and snake_case from external sources
            from_name = simplified_tag.get('from_name') or simplified_tag.get('fromName')
            to_name = simplified_tag.get('to_name') or simplified_tag.get('toName')
            values = simplified_tag.get('values')
            tag_id = simplified_tag.get('id')  # Use existing ID if provided
            
            if not from_name or not to_name:
                logger.warning(f"Skipping tag with missing from_name or to_name: {simplified_tag}")
                continue
            
            # Look up the type from template configuration
            control_type = self.get_type_for_from_name(from_name)
            
            if not control_type:
                logger.warning(
                    f"Could not find type for from_name '{from_name}' in template. "
                    f"Tag will be skipped. Available controls: {list(self._type_map.keys())}"
                )
                continue
            
            # Generate ID if not provided
            if not tag_id:
                tag_id = str(uuid.uuid4())
            
            # Convert values to the proper nested structure
            # The key in the value dict should match the control type
            full_tag = {
                "id": tag_id,
                "from_name": from_name,
                "to_name": to_name,
                "type": control_type,
                "value": {
                    control_type: values
                }
            }
            
            full_tags.append(full_tag)
            logger.debug(f"Converted tag: {from_name} ({control_type}) with {len(values) if isinstance(values, list) else 1} values")
        
        return full_tags
    
    def is_simplified_format(self, tag: Dict[str, Any]) -> bool:
        """
        Check if a tag is in simplified format (missing type field)
        
        Args:
            tag: Tag dictionary to check
            
        Returns:
            True if tag appears to be in simplified format
        """
        # Simplified format has 'values' at top level and no 'type' field
        has_values = 'values' in tag
        has_type = 'type' in tag
        has_value = 'value' in tag
        
        # If it has 'values' but no 'type', it's simplified
        # If it has 'type' and nested 'value', it's already full format
        return has_values and not has_type and not has_value
    
    def convert_if_needed(
        self, 
        tags: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert tags to full format if they are in simplified format
        
        This method can handle mixed formats - it will convert simplified tags
        and pass through tags that are already in full format.
        
        Args:
            tags: List of tags in either format
            
        Returns:
            List of tags in full internal format
        """
        if not tags:
            return []
        
        result = []
        
        for tag in tags:
            if self.is_simplified_format(tag):
                # Convert simplified format
                converted = self.convert_simplified_to_full([tag])
                result.extend(converted)
            else:
                # Already in full format, pass through
                result.append(tag)
        
        return result


def create_converter_from_template_config(
    template_config_dict: Dict[str, Any]
) -> TagFormatConverter:
    """
    Create a TagFormatConverter from a template configuration dictionary
    
    Args:
        template_config_dict: Template configuration as dict (from database JSON)
        
    Returns:
        TagFormatConverter instance
        
    Raises:
        ValueError: If template configuration is invalid
    """
    try:
        # Parse the configuration using Pydantic model
        from ..schema.template import TemplateConfiguration
        
        template_config = TemplateConfiguration(**template_config_dict)
        return TagFormatConverter(template_config)
    except Exception as e:
        logger.error(f"Failed to create tag converter from template config: {e}")
        raise ValueError(f"Invalid template configuration: {e}")
