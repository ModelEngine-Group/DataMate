#!/usr/bin/env python3
"""
1_5_anomaly_filter.py

执行顺序：第 1.5 步（可选）
- 在 normalization 之后、fast_lang_id 之前，对音频做快速异常检测与过滤。
- 默认扫描 output_data/normalization 目录，输出带 quality_flag 的 jsonl 列表。

用法示例：
  python -m src.pipeline.1_5_anomaly_filter
  python -m src.pipeline.1_5_anomaly_filter --audio_dir ./output_data/normalization --min_dur 0.5
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import anomaly_filter  # type: ignore


if __name__ == "__main__":
    raise SystemExit(anomaly_filter.main())

