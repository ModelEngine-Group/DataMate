#!/usr/bin/env python3
"""
2_denoise.py

执行顺序：第 2 步
- 调用 src.utils.gtcrn_denoise，对 output_data/normalization 下的音频做本地智能降噪，
  输出到 output_data/denoise。
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))

from src.utils import gtcrn_denoise  # type: ignore

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


def main() -> int:
    print_header("GTCRN 智能降噪")
    print_info("调用 src.utils.gtcrn_denoise 执行本地降噪 ...")

    input_dir = PROJECT_ROOT / "output_data" / "normalization"
    model_path = PROJECT_ROOT / "models" / "gtcrn" / "gtcrn.onnx"
    output_dir = PROJECT_ROOT / "output_data" / "denoise"

    argv_backup = sys.argv[:]
    try:
        sys.argv = [
            sys.argv[0],
            "--input", str(input_dir),
            "--model", str(model_path),
            "--output", str(output_dir),
        ]
        code = gtcrn_denoise.main()
    finally:
        sys.argv = argv_backup

    if code == 0:
        print_success("GTCRN 降噪执行完成。")
    else:
        print_error(f"GTCRN 降噪执行失败，返回码: {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

