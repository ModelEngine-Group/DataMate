"""Security utilities for handling sensitive data"""
import re
from typing import Any, Dict


SENSITIVE_FIELDS = [
    "secretKey",
    "accessKey",
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "apiKey",
    "api_key",
    "access_key",
    "secret_key",
]

MASK_PATTERN = "**********"


def mask_sensitive_value(value: str) -> str:
    """Mask a single sensitive value"""
    return MASK_PATTERN


def is_masked_value(value: str) -> bool:
    """Check if a value is already masked"""
    return value == MASK_PATTERN


def preserve_sensitive_values(
    new_config: Dict[str, Any], 
    original_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Preserve original sensitive values if masked pattern is detected in update request.
    
    When frontend receives masked values and sends them back in update request,
    this function detects masked values and replaces them with original values
    from database.
    
    Args:
        new_config: Config from update request (may contain masked values)
        original_config: Original config from database (contains real values)
        
    Returns:
        Config with original sensitive values preserved
    """
    if not isinstance(new_config, dict) or not isinstance(original_config, dict):
        return new_config
    
    preserved_config = {}
    for key, new_value in new_config.items():
        # Check if key is a sensitive field
        key_lower = key.lower()
        is_sensitive = any(
            field.lower() == key_lower or field.lower() in key_lower
            for field in SENSITIVE_FIELDS
        )
        
        # If value is masked and field is sensitive, use original value
        if is_sensitive and isinstance(new_value, str) and is_masked_value(new_value):
            original_value = original_config.get(key)
            preserved_config[key] = original_value if original_value else new_value
        elif isinstance(new_value, dict):
            # Recursively process nested dictionaries
            original_nested = original_config.get(key, {})
            preserved_config[key] = preserve_sensitive_values(new_value, original_nested)
        elif isinstance(new_value, list):
            # Process list items (preserve original if matching structure)
            original_list = original_config.get(key, [])
            preserved_config[key] = [
                preserve_sensitive_values(new_item, orig_item) 
                if isinstance(new_item, dict) and isinstance(orig_item, dict)
                else new_item
                for new_item, orig_item in zip(new_value, original_list)
            ] if len(new_value) == len(original_list) else new_value
        else:
            # Keep non-sensitive/non-masked values
            preserved_config[key] = new_value
    
    return preserved_config


def mask_sensitive_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively mask sensitive fields in a dictionary.
    
    Args:
        data: Dictionary that may contain sensitive fields
        
    Returns:
        Dictionary with sensitive values masked
    """
    if not isinstance(data, dict):
        return data
    
    masked_data = {}
    for key, value in data.items():
        # Check if the key is a sensitive field (case-insensitive)
        key_lower = key.lower()
        is_sensitive = any(
            field.lower() == key_lower or field.lower() in key_lower
            for field in SENSITIVE_FIELDS
        )
        
        if is_sensitive and isinstance(value, str):
            # Mask the sensitive value
            masked_data[key] = MASK_PATTERN
        elif isinstance(value, dict):
            # Recursively mask nested dictionaries
            masked_data[key] = mask_sensitive_dict(value)
        elif isinstance(value, list):
            # Process list items
            masked_data[key] = [
                mask_sensitive_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Keep non-sensitive values as-is
            masked_data[key] = value
    
    return masked_data


def mask_sensitive_info(text: str) -> str:
    """
    Mask sensitive information in text by replacing values with **********
    
    Args:
        text: Original text that may contain sensitive information
        
    Returns:
        Text with sensitive values masked
    """
    masked_text = text
    
    for field in SENSITIVE_FIELDS:
        patterns = [
            rf'"{field}"\s*:\s*"[^"]*"',
            rf'"{field}"\s*:\s*"[^"]*"',
            rf'{field}\s*=\s*[^\s,\]]+',
            rf"'{field}'\s*:\s*'[^']*'",
        ]
        
        for pattern in patterns:
            if '"' in pattern:
                masked_text = re.sub(pattern, f'"{field}": "{MASK_PATTERN}"', masked_text)
            elif "'" in pattern:
                masked_text = re.sub(pattern, f"'{field}': '{MASK_PATTERN}'", masked_text)
            else:
                masked_text = re.sub(pattern, f'{field}={MASK_PATTERN}', masked_text)
    
    return masked_text