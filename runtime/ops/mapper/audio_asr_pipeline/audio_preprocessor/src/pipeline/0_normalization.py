#!/usr/bin/env python3
"""
1_normalization.py

执行顺序：第 1 步
- 调用 src.pipeline.normalization 完成音频标准化。
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import normalization  # type: ignore


if __name__ == "__main__":
    raise SystemExit(normalization.main())

