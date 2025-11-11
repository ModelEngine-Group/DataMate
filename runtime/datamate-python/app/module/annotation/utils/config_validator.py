"""
Label Studio Configuration Validation Utilities
"""
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET
from app.module.annotation.config import LabelStudioTagConfig


class LabelStudioConfigValidator:
    """验证Label Studio配置的工具类"""
    
    @staticmethod
    def _get_config() -> LabelStudioTagConfig:
        """获取标签配置实例"""
        return LabelStudioTagConfig()
    
    @staticmethod
    def validate_xml(xml_string: str) -> Tuple[bool, Optional[str]]:
        """
        验证XML格式是否正确
        
        Args:
            xml_string: Label Studio XML配置字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            config = LabelStudioConfigValidator._get_config()
            root = ET.fromstring(xml_string)
            
            # 检查根元素
            if root.tag != 'View':
                return False, "Root element must be <View>"
            
            # 检查是否有对象定义
            object_types = config.get_object_types()
            objects = [child for child in root if child.tag in object_types]
            if not objects:
                return False, "No data objects (Image, Text, etc.) found"
            
            # 检查是否有控件定义
            control_types = config.get_control_types()
            controls = [child for child in root if child.tag in control_types]
            if not controls:
                return False, "No annotation controls found"
            
            # 验证每个控件
            for control in controls:
                valid, error = LabelStudioConfigValidator._validate_control(control)
                if not valid:
                    return False, f"Control {control.tag}: {error}"
            
            return True, None
            
        except ET.ParseError as e:
            return False, f"XML parse error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def _validate_control(control: ET.Element) -> Tuple[bool, Optional[str]]:
        """
        验证单个控件元素
        
        Args:
            control: 控件XML元素
            
        Returns:
            (是否有效, 错误信息)
        """
        config = LabelStudioConfigValidator._get_config()
        
        # 检查必需属性
        if 'name' not in control.attrib:
            return False, "Missing 'name' attribute"
        
        if 'toName' not in control.attrib:
            return False, "Missing 'toName' attribute"
        
        # 检查控件是否需要子元素
        if config.requires_children(control.tag):
            child_tag = config.get_child_tag(control.tag)
            if not child_tag:
                return False, f"Configuration error: no child_tag defined for {control.tag}"
            
            children = control.findall(child_tag)
            if not children:
                return False, f"{control.tag} must have at least one <{child_tag}> child"
            
            # 检查每个子元素是否有value
            for child in children:
                if 'value' not in child.attrib:
                    return False, f"{child_tag} missing 'value' attribute"
        
        return True, None
    
    @staticmethod
    def extract_label_values(xml_string: str) -> Dict[str, List[str]]:
        """
        从XML中提取所有标签值
        
        Args:
            xml_string: Label Studio XML配置字符串
            
        Returns:
            字典，键为控件名称，值为标签值列表
        """
        result = {}
        config = LabelStudioConfigValidator._get_config()
        
        try:
            root = ET.fromstring(xml_string)
            control_types = config.get_control_types()
            controls = [child for child in root if child.tag in control_types]
            
            for control in controls:
                if not config.requires_children(control.tag):
                    continue
                    
                control_name = control.get('name', 'unknown')
                child_tag = config.get_child_tag(control.tag)
                
                if child_tag:
                    children = control.findall(child_tag)
                    label_values = [child.get('value', '') for child in children]
                    result[control_name] = label_values
                
        except Exception:
            pass
        
        return result
    
    @staticmethod
    def validate_configuration_json(config: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证配置JSON结构
        
        Args:
            config: 配置字典
            
        Returns:
            (是否有效, 错误信息)
        """
        # 检查必需字段
        if 'labels' not in config:
            return False, "Missing 'labels' field"
        
        if 'objects' not in config:
            return False, "Missing 'objects' field"
        
        if not isinstance(config['labels'], list):
            return False, "'labels' must be an array"
        
        if not isinstance(config['objects'], list):
            return False, "'objects' must be an array"
        
        if not config['labels']:
            return False, "'labels' array cannot be empty"
        
        if not config['objects']:
            return False, "'objects' array cannot be empty"
        
        # 验证每个标签定义
        for idx, label in enumerate(config['labels']):
            valid, error = LabelStudioConfigValidator._validate_label_definition(label)
            if not valid:
                return False, f"Label {idx}: {error}"
        
        # 验证每个对象定义
        for idx, obj in enumerate(config['objects']):
            valid, error = LabelStudioConfigValidator._validate_object_definition(obj)
            if not valid:
                return False, f"Object {idx}: {error}"
        
        # 验证toName引用
        object_names = {obj['name'] for obj in config['objects']}
        for label in config['labels']:
            to_name = label.get('toName') or label.get('to_name')
            from_name = label.get('fromName') or label.get('from_name')
            if to_name not in object_names:
                return False, f"Label '{from_name}' references unknown object '{to_name}'"
        
        return True, None
    
    @staticmethod
    def _validate_label_definition(label: Dict) -> Tuple[bool, Optional[str]]:
        """验证标签定义"""
        config = LabelStudioConfigValidator._get_config()
        control_types = config.get_control_types()
        
        # Support both camelCase and snake_case
        from_name = label.get('fromName') or label.get('from_name')
        to_name = label.get('toName') or label.get('to_name')
        label_type = label.get('type')
        
        if not from_name:
            return False, "Missing required field 'fromName'"
        if not to_name:
            return False, "Missing required field 'toName'"
        if not label_type:
            return False, "Missing required field 'type'"
        
        # 检查类型是否支持
        if label_type not in control_types:
            return False, f"Unsupported control type '{label_type}'"
        
        # 检查是否需要子元素(options 或 labels)
        if config.requires_children(label_type):
            if 'options' not in label and 'labels' not in label:
                return False, f"{label_type} must have 'options' or 'labels' field"
        
        return True, None
    
    @staticmethod
    def _validate_object_definition(obj: Dict) -> Tuple[bool, Optional[str]]:
        """验证对象定义"""
        config = LabelStudioConfigValidator._get_config()
        object_types = config.get_object_types()
        
        required_fields = ['name', 'type', 'value']
        
        for field in required_fields:
            if field not in obj:
                return False, f"Missing required field '{field}'"
        
        # 检查类型是否支持
        if obj['type'] not in object_types:
            return False, f"Unsupported object type '{obj['type']}'"
        
        # 检查value格式
        if not obj['value'].startswith('$'):
            return False, "Object value must start with '$' (e.g., '$image')"
        
        return True, None


# 使用示例
if __name__ == "__main__":
    # 验证XML
    xml = """<View>
  <Image name="image" value="$image"/>
  <Choices name="choice" toName="image" required="true">
    <Label value="Cat"/>
    <Label value="Dog"/>
  </Choices>
</View>"""
    
    valid, error = LabelStudioConfigValidator.validate_xml(xml)
    print(f"XML Valid: {valid}, Error: {error}")
    
    # 验证配置JSON
    config = {
        "labels": [
            {
                "fromName": "choice",
                "toName": "image",
                "type": "Choices",
                "options": ["Cat", "Dog"],
                "required": True
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
    
    valid, error = LabelStudioConfigValidator.validate_configuration_json(config)
    print(f"Config Valid: {valid}, Error: {error}")
