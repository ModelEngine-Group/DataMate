#!/usr/bin/env python3
"""
Example: Tag Format Conversion Usage

This script demonstrates how to use the tag format conversion feature
to update file tags using the simplified external format.

Run this script after:
1. Creating a dataset
2. Creating an annotation template
3. Creating a labeling project that links the dataset and template
4. Uploading files to the dataset
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"
FILE_ID = "your-file-uuid-here"  # Replace with actual file ID


async def update_file_tags_simplified(
    file_id: str,
    tags: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Update file tags using simplified format
    
    Args:
        file_id: UUID of the file to update
        tags: List of tags in simplified format
        
    Returns:
        API response
    """
    url = f"{API_BASE_URL}/api/annotation/task/{file_id}"
    
    payload = {
        "tags": tags
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()


async def example_1_basic_update():
    """Example 1: Basic tag update with simplified format"""
    print("\n=== Example 1: Basic Tag Update ===\n")
    
    # Simplified format - no type or nested value required
    tags = [
        {
            "from_name": "sentiment",
            "to_name": "text",
            "values": ["positive", "negative"]
        }
    ]
    
    print("Submitting tags in simplified format:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        
        print("\n✓ Success! Response:")
        print(json.dumps(result, indent=2))
        
        # The response will contain tags in full internal format
        if result.get("data", {}).get("tags"):
            stored_tag = result["data"]["tags"][0]
            print("\n📝 Stored tag format:")
            print(f"   - ID: {stored_tag.get('id')}")
            print(f"   - Type: {stored_tag.get('type')}")
            print(f"   - Value: {stored_tag.get('value')}")
            
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_2_multiple_controls():
    """Example 2: Update multiple different control types"""
    print("\n=== Example 2: Multiple Control Types ===\n")
    
    tags = [
        # Text classification
        {
            "from_name": "sentiment",
            "to_name": "text",
            "values": ["positive"]
        },
        # Image bounding boxes
        {
            "from_name": "bbox",
            "to_name": "image",
            "values": ["cat", "dog"]
        },
        # Text comment
        {
            "from_name": "comment",
            "to_name": "text",
            "values": ["This is a great example"]
        }
    ]
    
    print("Submitting multiple control types:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        print("\n✓ Success! All tags converted and stored.")
        print(f"   Total tags: {len(result['data']['tags'])}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_3_update_existing():
    """Example 3: Update existing tag by preserving ID"""
    print("\n=== Example 3: Update Existing Tag ===\n")
    
    # First, let's assume we know the ID of an existing tag
    existing_tag_id = "some-existing-uuid"
    
    tags = [
        {
            "id": existing_tag_id,  # Preserve ID to update, not create new
            "from_name": "sentiment",
            "to_name": "text",
            "values": ["neutral"]  # Change value
        }
    ]
    
    print("Updating existing tag by ID:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        print("\n✓ Success! Existing tag updated.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_4_camelcase():
    """Example 4: Using camelCase field names (frontend style)"""
    print("\n=== Example 4: CamelCase Field Names ===\n")
    
    # Frontend typically sends camelCase
    tags = [
        {
            "fromName": "sentiment",  # camelCase
            "toName": "text",         # camelCase
            "values": ["positive"]
        }
    ]
    
    print("Submitting with camelCase:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        print("\n✓ Success! CamelCase automatically handled.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_5_mixed_format():
    """Example 5: Mixed format - some simplified, some full"""
    print("\n=== Example 5: Mixed Format Support ===\n")
    
    tags = [
        # Simplified format
        {
            "from_name": "new_label",
            "to_name": "image",
            "values": ["new_value"]
        },
        # Full format (already has type and nested value)
        {
            "id": "existing-uuid-123",
            "from_name": "old_label",
            "to_name": "image",
            "type": "choices",
            "value": {
                "choices": ["old_value"]
            }
        }
    ]
    
    print("Submitting mixed format:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        print("\n✓ Success! Mixed format handled correctly.")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def example_6_error_handling():
    """Example 6: Error handling - unknown control"""
    print("\n=== Example 6: Error Handling ===\n")
    
    tags = [
        # Valid control
        {
            "from_name": "sentiment",
            "to_name": "text",
            "values": ["positive"]
        },
        # Invalid control - doesn't exist in template
        {
            "from_name": "unknown_control",
            "to_name": "text",
            "values": ["some_value"]
        }
    ]
    
    print("Submitting with unknown control:")
    print(json.dumps(tags, indent=2))
    
    try:
        result = await update_file_tags_simplified(FILE_ID, tags)
        print("\n⚠ Partial Success:")
        print(f"   Valid tags stored: {len(result['data']['tags'])}")
        print("   (Unknown control was skipped)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("Tag Format Conversion Examples")
    print("="*60)
    
    print(f"\nAPI Base URL: {API_BASE_URL}")
    print(f"File ID: {FILE_ID}")
    print("\n⚠ Make sure to replace FILE_ID with an actual file UUID!")
    
    # Uncomment the examples you want to run:
    
    # await example_1_basic_update()
    # await example_2_multiple_controls()
    # await example_3_update_existing()
    # await example_4_camelcase()
    # await example_5_mixed_format()
    # await example_6_error_handling()
    
    print("\n" + "="*60)
    print("Tip: Edit this script to uncomment examples you want to run")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
