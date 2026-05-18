#!/usr/bin/env python3
"""
2_fast_lang_id.py

执行顺序：第 2 步
- 调用 src.utils.fast_lang_id，使用 SpeechBrain 快速识别中/英文，
  默认读取 output_data/normalization，生成 output_data/lid/item_with_lang.list。
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))

from src.utils import fast_lang_id  # type: ignore

try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore

    def print_info(msg: str):
        print(info(msg))

    def print_error(msg: str):
        print(error(msg))

    def print_success(msg: str):
        print(success(msg))

    def print_header(msg: str):
        print(header(msg))

except Exception:
    def print_info(msg: str):
        print(f"[INFO] {msg}")

    def print_error(msg: str):
        print(f"[ERROR] {msg}")

    def print_success(msg: str):
        print(f"[SUCCESS] {msg}")

    def print_header(msg: str):
        print(f"=== {msg} ===")


if __name__ == "__main__":
    
    code = fast_lang_id.main()
    if code == 0:
        pass
    else:
        print_error(f"fast_lang_id 执行失败，返回码: {code}")
    raise SystemExit(code)


