"""Image object detection (YOLOv8) operator package.

This package exposes the ImageObjectDetectionBoundingBox annotator so that
the auto-annotation worker can import it via different module paths.
"""

from .process import ImageObjectDetectionBoundingBox

__all__ = ["ImageObjectDetectionBoundingBox"]
