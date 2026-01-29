"""
步骤二：文档生成
"""

__version__ = "1.0.0"

try:
    from .doc_generator import DocGenerator
except ImportError:
    from doc_generator import DocGenerator

__all__ = ["DocGenerator"]
