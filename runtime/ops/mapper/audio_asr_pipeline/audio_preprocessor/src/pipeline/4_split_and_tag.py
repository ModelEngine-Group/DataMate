#!/usr/bin/env python3
"""
3_split_and_tag.py

执行顺序：第 3 步
- 调用 src.pipeline.split_and_tag，将 normalization 结果切分为 ≤2min 片段并生成 split 清单。
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import split_and_tag  # type: ignore


if __name__ == "__main__":
    raise SystemExit(split_and_tag.main())

