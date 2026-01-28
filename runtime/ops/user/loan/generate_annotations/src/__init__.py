"""
步骤五：图文对生成
"""

__version__ = "1.0.0"

try:
    from .annotation_builder import AnnotationBuilder
except ImportError:
    from annotation_builder import AnnotationBuilder

__all__ = ["AnnotationBuilder"]
