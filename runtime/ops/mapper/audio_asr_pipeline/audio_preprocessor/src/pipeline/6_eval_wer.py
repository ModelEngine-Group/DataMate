#!/usr/bin/env python3
"""
6_eval_wer.py

执行顺序：第 6 步（可选）
- 调用 src.pipeline.eval_wer：
  - 计算中文 CER、英文 WER
  - 生成 output_data/validation/transcript_log.txt
"""

from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import eval_wer  # type: ignore


if __name__ == "__main__":
    # 统一工作目录到项目根目录，避免 YAML/CLI 里使用相对路径时找不到文件
    os.chdir(PROJECT_ROOT)
    raise SystemExit(eval_wer.main())

