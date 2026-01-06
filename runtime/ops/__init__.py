# -*- coding: utf-8 -*-
"""Datamate built-in operators package.

This package contains built-in operators for filtering, slicing, annotation, etc.
It is mounted into the runtime container under ``datamate.ops`` so that
``from datamate.ops.annotation...`` imports work correctly.
"""

__all__ = [
    "annotation",
    "filter",
    "formatter",
    "llms",
    "mapper",
    "slicer",
    "user",
]
