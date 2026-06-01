#!/usr/bin/env python3
"""
配置加载模块
负责定位和加载 audio_config.yaml 配置文件
支持通过命令行参数指定配置文件
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def find_config_file(config_path: Optional[str] = None) -> Path:
    """
    定位配置文件，按以下优先级查找：
    1. 如果提供了 config_path 参数，直接使用它
    2. 当前工作目录的 config/audio_config.yaml
    3. 脚本所在目录的上一级 config/audio_config.yaml
    4. 用户主目录的 .audio_preprocessor/audio_config.yaml
    
    Args:
        config_path: 用户指定的配置文件路径，可选
        
    Returns:
        Path: 配置文件的路径
    """
    # 如果提供了配置路径，直接使用
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"指定的配置文件不存在: {path}")
        return path
    
    # 否则按默认优先级查找
    search_paths = [
        # 当前工作目录下的 config 子目录
        Path.cwd() / "config" / "audio_config.yaml",
        # 脚本所在目录的上一级 config 目录
        Path(__file__).parent.parent.parent / "config" / "audio_config.yaml",
        # 用户主目录的配置目录
        Path.home() / ".audio_preprocessor" / "audio_config.yaml",
    ]
    
    for config_path in search_paths:
        if config_path.exists():
            return config_path
    
    # 如果都找不到，返回默认路径（用于创建示例配置）
    return search_paths[1]


def load_audio_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载音频配置文件
    
    Args:
        config_path: 用户指定的配置文件路径，可选
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    config_file = find_config_file(config_path)
    
    # 如果配置文件不存在，创建默认配置并提示
    if not config_file.exists():
        create_default_config(config_file)
        print(f"[INFO] 配置文件不存在，已创建默认配置: {config_file}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 检查配置文件结构
        if 'audio_config' not in config_data:
            config = config_data  # 如果是顶级配置
        else:
            config = config_data['audio_config']
        
        # 验证必要配置项
        required_keys = ['output_format', 'channels', 'sample_rate', 
                        'sample_width', 'encoding', 'input_format']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"配置文件中缺少必要的键: {key}")
        
        return config
        
    except yaml.YAMLError as e:
        raise ValueError(f"配置文件格式错误: {config_file}") from e


def create_default_config(config_path: Path) -> None:
    """创建默认配置文件"""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        'audio_config': {
            'output_format': 'wav',
            'channels': 1,
            'sample_rate': 16000,
            'sample_width': 2,
            'encoding': 'pcm_s16le',
            'input_format': ['mp3', 'wav', 'aac', 'm4a', 'flac'],
            'quality_checks': {
                'min_duration_seconds': 0.5,
                'max_duration_seconds': 30.0,
                'max_silence_ratio': 0.3
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'audio_conversion.log'
            }
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, default_flow_style=False, 
                  allow_unicode=True, indent=2)


# 全局配置变量（惰性加载）
_AUDIO_CONFIG = None
_CONFIG_PATH = None


def get_audio_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """获取音频配置（单例模式）
    
    Args:
        config_path: 用户指定的配置文件路径，可选
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    global _AUDIO_CONFIG, _CONFIG_PATH
    
    # 如果提供了新路径或之前没有加载过，重新加载配置
    if config_path is not None or _AUDIO_CONFIG is None:
        _AUDIO_CONFIG = load_audio_config(config_path)
        if config_path:
            _CONFIG_PATH = config_path
    
    return _AUDIO_CONFIG


def clear_config_cache() -> None:
    """清除配置缓存，强制重新加载"""
    global _AUDIO_CONFIG, _CONFIG_PATH
    _AUDIO_CONFIG = None
    _CONFIG_PATH = None