"""
Unit tests for TagFormatConverter

Run with: pytest app/module/annotation/utils/test_tag_converter.py -v
"""

import pytest
from .tag_converter import TagFormatConverter, create_converter_from_template_config
from ..schema.template import TemplateConfiguration, LabelDefinition, ObjectDefinition


@pytest.fixture
def sample_template_config():
    """Create a sample template configuration for testing"""
    return TemplateConfiguration(
        labels=[
            LabelDefinition(
                fromName="sentiment",
                toName="text",
                type="choices",
                options=["positive", "negative", "neutral"],
                required=True,
                labels=None,
                description=None
            ),
            LabelDefinition(
                fromName="bbox",
                toName="image",
                type="rectanglelabels",
                labels=["cat", "dog", "bird"],
                required=False,
                options=None,
                description=None
            ),
            LabelDefinition(
                fromName="comment",
                toName="text",
                type="textarea",
                required=False,
                options=None,
                labels=None,
                description=None
            )
        ],
        objects=[
            ObjectDefinition(name="text", type="Text", value="$text"),
            ObjectDefinition(name="image", type="Image", value="$image")
        ],
        metadata=None
    )


@pytest.fixture
def converter(sample_template_config):
    """Create a converter instance"""
    return TagFormatConverter(sample_template_config)


class TestTagFormatConverter:
    """Test TagFormatConverter functionality"""
    
    def test_type_map_building(self, converter):
        """Test that type map is built correctly from template"""
        assert converter.get_type_for_from_name("sentiment") == "choices"
        assert converter.get_type_for_from_name("bbox") == "rectanglelabels"
        assert converter.get_type_for_from_name("comment") == "textarea"
        assert converter.get_type_for_from_name("nonexistent") is None
    
    def test_convert_simplified_to_full_single_value(self, converter):
        """Test conversion of simplified format with single value"""
        simplified = [
            {
                "from_name": "sentiment",
                "to_name": "text",
                "values": ["positive"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 1
        tag = result[0]
        assert tag["from_name"] == "sentiment"
        assert tag["to_name"] == "text"
        assert tag["type"] == "choices"
        assert tag["value"] == {"choices": ["positive"]}
        assert "id" in tag
    
    def test_convert_simplified_to_full_multiple_values(self, converter):
        """Test conversion of simplified format with multiple values"""
        simplified = [
            {
                "from_name": "bbox",
                "to_name": "image",
                "values": ["cat", "dog"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 1
        tag = result[0]
        assert tag["type"] == "rectanglelabels"
        assert tag["value"] == {"rectanglelabels": ["cat", "dog"]}
    
    def test_convert_simplified_camelcase(self, converter):
        """Test that camelCase field names are supported"""
        simplified = [
            {
                "fromName": "sentiment",  # camelCase
                "toName": "text",         # camelCase
                "values": ["neutral"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 1
        assert result[0]["from_name"] == "sentiment"
        assert result[0]["to_name"] == "text"
    
    def test_convert_multiple_tags(self, converter):
        """Test conversion of multiple tags at once"""
        simplified = [
            {
                "from_name": "sentiment",
                "to_name": "text",
                "values": ["positive"]
            },
            {
                "from_name": "bbox",
                "to_name": "image",
                "values": ["cat"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 2
        assert result[0]["type"] == "choices"
        assert result[1]["type"] == "rectanglelabels"
    
    def test_convert_with_existing_id(self, converter):
        """Test that existing IDs are preserved"""
        existing_id = "my-custom-id-123"
        simplified = [
            {
                "id": existing_id,
                "from_name": "sentiment",
                "to_name": "text",
                "values": ["positive"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert result[0]["id"] == existing_id
    
    def test_skip_unknown_from_name(self, converter):
        """Test that tags with unknown from_name are skipped"""
        simplified = [
            {
                "from_name": "unknown_control",
                "to_name": "text",
                "values": ["value"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 0  # Should be skipped
    
    def test_skip_missing_fields(self, converter):
        """Test that tags with missing required fields are skipped"""
        simplified = [
            {
                "from_name": "sentiment",
                # Missing to_name
                "values": ["positive"]
            }
        ]
        
        result = converter.convert_simplified_to_full(simplified)
        
        assert len(result) == 0  # Should be skipped
    
    def test_is_simplified_format(self, converter):
        """Test detection of simplified format"""
        # Simplified format
        assert converter.is_simplified_format({
            "from_name": "x",
            "to_name": "y",
            "values": ["a"]
        }) is True
        
        # Full format
        assert converter.is_simplified_format({
            "id": "123",
            "from_name": "x",
            "to_name": "y",
            "type": "choices",
            "value": {"choices": ["a"]}
        }) is False
        
        # Edge case: has both (should not be considered simplified)
        assert converter.is_simplified_format({
            "from_name": "x",
            "to_name": "y",
            "type": "choices",
            "values": ["a"]
        }) is False
    
    def test_convert_if_needed_mixed_formats(self, converter):
        """Test conversion of mixed format tags"""
        mixed = [
            # Simplified format
            {
                "from_name": "sentiment",
                "to_name": "text",
                "values": ["positive"]
            },
            # Full format
            {
                "id": "existing-123",
                "from_name": "bbox",
                "to_name": "image",
                "type": "rectanglelabels",
                "value": {"rectanglelabels": ["cat"]}
            }
        ]
        
        result = converter.convert_if_needed(mixed)
        
        assert len(result) == 2
        # First should be converted
        assert result[0]["type"] == "choices"
        assert result[0]["value"] == {"choices": ["positive"]}
        # Second should pass through unchanged
        assert result[1]["id"] == "existing-123"
        assert result[1]["type"] == "rectanglelabels"


class TestCreateConverterFromDict:
    """Test the factory function for creating converter from dict"""
    
    def test_create_from_valid_dict(self):
        """Test creating converter from valid configuration dict"""
        config_dict = {
            "labels": [
                {
                    "fromName": "label",
                    "toName": "image",
                    "type": "choices",
                    "options": ["a", "b"]
                }
            ],
            "objects": [
                {
                    "name": "image",
                    "type": "Image",
                    "value": "$image"
                }
            ]
        }
        
        converter = create_converter_from_template_config(config_dict)
        
        assert isinstance(converter, TagFormatConverter)
        assert converter.get_type_for_from_name("label") == "choices"
    
    def test_create_from_invalid_dict(self):
        """Test that invalid config raises ValueError"""
        invalid_config = {
            "labels": "not-a-list",  # Should be a list
            "objects": []
        }
        
        with pytest.raises(ValueError, match="Invalid template configuration"):
            create_converter_from_template_config(invalid_config)


class TestIntegrationScenarios:
    """Test real-world usage scenarios"""
    
    def test_external_api_submission(self, converter):
        """Simulate external user submitting tags via API"""
        # User submits simplified format
        user_submission = [
            {
                "fromName": "sentiment",  # User uses camelCase
                "toName": "text",
                "values": ["positive", "negative"]
            }
        ]
        
        # System converts to internal format
        internal_tags = converter.convert_if_needed(user_submission)
        
        # Verify correct storage format
        assert len(internal_tags) == 1
        assert internal_tags[0]["type"] == "choices"
        assert internal_tags[0]["value"] == {"choices": ["positive", "negative"]}
        assert "id" in internal_tags[0]
    
    def test_update_existing_tags(self, converter):
        """Simulate updating existing tags with new values"""
        # Existing tags in database (full format)
        existing_tags = [
            {
                "id": "tag-001",
                "from_name": "sentiment",
                "to_name": "text",
                "type": "choices",
                "value": {"choices": ["positive"]}
            }
        ]
        
        # User updates with simplified format
        update_request = [
            {
                "id": "tag-001",  # Same ID to update
                "from_name": "sentiment",
                "to_name": "text",
                "values": ["negative"]  # New value
            }
        ]
        
        # Convert update request
        converted_update = converter.convert_if_needed(update_request)
        
        # Merge logic would replace tag-001
        assert converted_update[0]["id"] == "tag-001"
        assert converted_update[0]["value"] == {"choices": ["negative"]}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
