#!/usr/bin/env python3
"""
7_eval_keyword_recall.py

执行顺序：可在评估阶段（例如第 7 步）
- 调用 src.pipeline.eval_keyword_recall：
  - 读取中英文关键词列表
  - 使用 output_data/asr/merged_text.txt 的识别结果
  - 计算关键词召回率并生成报告 output_data/validation/keyword_recall.txt
"""

from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import eval_keyword_recall  # type: ignore


if __name__ == "__main__":
    # 统一工作目录到项目根目录，避免 YAML/CLI 里使用相对路径时找不到文件
    os.chdir(PROJECT_ROOT)
    raise SystemExit(eval_keyword_recall.main())

