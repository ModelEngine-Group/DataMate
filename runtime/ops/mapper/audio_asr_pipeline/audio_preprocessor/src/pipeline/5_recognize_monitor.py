#!/usr/bin/env python3
"""
4_recognize_monitor.py

执行顺序：第 4 步
- 调用 src.pipeline.recognize_monitor：
  - 先识别中文片段，再识别英文片段
  - 合并为 output_data/asr/merged_text.txt
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import recognize_monitor  # type: ignore


if __name__ == "__main__":
    raise SystemExit(recognize_monitor.main())

