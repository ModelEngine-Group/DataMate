"""
步骤一：数据生成
"""

__version__ = "1.0.0"

try:
    from .data_generator import DataGenerator
except ImportError:
    from data_generator import DataGenerator

__all__ = ["DataGenerator"]
