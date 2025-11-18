"""
Label Studio Tag Configuration Loader
"""
import yaml
from typing import Dict, Any, Optional, Set, Tuple
from pathlib import Path


class LabelStudioTagConfig:
    """Label Studio标签配置管理器"""
    
    _instance: Optional['LabelStudioTagConfig'] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化时加载配置"""
        if not self._config:
            self._load_config()
    
    @classmethod
    def _load_config(cls):
        """加载YAML配置文件"""
        config_path = Path(__file__).parent / "label_studio_tags.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            cls._config = yaml.safe_load(f) or {}
    
    @classmethod
    def get_object_types(cls) -> Set[str]:
        """获取所有支持的对象类型"""
        return set(cls._config.get('objects', {}).keys())
    
    @classmethod
    def get_control_types(cls) -> Set[str]:
        """获取所有支持的控件类型"""
        return set(cls._config.get('controls', {}).keys())
    
    @classmethod
    def get_control_config(cls, control_type: str) -> Optional[Dict[str, Any]]:
        """获取控件的配置信息"""
        return cls._config.get('controls', {}).get(control_type)
    
    @classmethod
    def get_object_config(cls, object_type: str) -> Optional[Dict[str, Any]]:
        """获取对象的配置信息"""
        return cls._config.get('objects', {}).get(object_type)
    
    @classmethod
    def requires_children(cls, control_type: str) -> bool:
        """检查控件是否需要子元素"""
        config = cls.get_control_config(control_type)
        return config.get('requires_children', False) if config else False
    
    @classmethod
    def get_child_tag(cls, control_type: str) -> Optional[str]:
        """获取控件的子元素标签名"""
        config = cls.get_control_config(control_type)
        return config.get('child_tag') if config else None
    
    @classmethod
    def get_controls_with_child_tag(cls, child_tag: str) -> Set[str]:
        """获取使用指定子元素标签的所有控件类型"""
        controls = set()
        for control_type, config in cls._config.get('controls', {}).items():
            if config.get('child_tag') == child_tag:
                controls.add(control_type)
        return controls
    
    @classmethod
    def get_optional_attrs(cls, tag_type: str, is_control: bool = True) -> Dict[str, Any]:
        """
        获取标签的可选属性配置
        
        Args:
            tag_type: 标签类型
            is_control: 是否为控件类型（否则为对象类型）
            
        Returns:
            可选属性配置字典
        """
        config = cls.get_control_config(tag_type) if is_control else cls.get_object_config(tag_type)
        if not config:
            return {}
        
        optional_attrs = config.get('optional_attrs', {})
        
        # 如果是简单列表格式（旧格式），转换为字典
        if isinstance(optional_attrs, list):
            return {attr: {} for attr in optional_attrs}
        
        # 确保返回的是字典
        return optional_attrs if isinstance(optional_attrs, dict) else {}
    
    @classmethod
    def validate_attr_value(cls, tag_type: str, attr_name: str, attr_value: Any, is_control: bool = True) -> Tuple[bool, Optional[str]]:
        """
        验证属性值是否符合配置要求
        
        Args:
            tag_type: 标签类型
            attr_name: 属性名
            attr_value: 属性值
            is_control: 是否为控件类型
            
        Returns:
            (是否有效, 错误信息)
        """
        optional_attrs = cls.get_optional_attrs(tag_type, is_control)
        
        if attr_name not in optional_attrs:
            return True, None  # 不在配置中的属性，不验证
        
        attr_config = optional_attrs.get(attr_name, {})
        
        # 如果配置不是字典，跳过验证
        if not isinstance(attr_config, dict):
            return True, None
        
        # 检查类型
        expected_type = attr_config.get('type')
        if expected_type == 'boolean':
            if not isinstance(attr_value, (bool, str)) or (isinstance(attr_value, str) and attr_value.lower() not in ['true', 'false']):
                return False, f"Attribute '{attr_name}' must be boolean"
        elif expected_type == 'number':
            try:
                float(attr_value)
            except (ValueError, TypeError):
                return False, f"Attribute '{attr_name}' must be a number"
        
        # 检查枚举值
        allowed_values = attr_config.get('values')
        if allowed_values and attr_value not in allowed_values:
            return False, f"Attribute '{attr_name}' must be one of {allowed_values}, got '{attr_value}'"
        
        return True, None
    
    @classmethod
    def get_attr_default(cls, tag_type: str, attr_name: str, is_control: bool = True) -> Optional[Any]:
        """获取属性的默认值"""
        optional_attrs = cls.get_optional_attrs(tag_type, is_control)
        attr_config = optional_attrs.get(attr_name, {})
        
        # 确保attr_config是字典后再访问
        if isinstance(attr_config, dict):
            return attr_config.get('default')
        return None
