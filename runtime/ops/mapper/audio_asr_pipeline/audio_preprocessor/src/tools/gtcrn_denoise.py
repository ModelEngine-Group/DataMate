#!/usr/bin/env python3
"""
GTCRN 独立降噪小工具

特点：
- 面向用户直接使用，默认更偏单文件/目录处理
- 支持本地 ONNX 模型，适合已下载权重的离线环境
- 可选导出 ONNX（当输入是 .tar/.pt/.pth 时）

默认参数：
- 输入：必填，可为单文件或目录
- 模型：`models/gtcrn/gtcrn.onnx`
- 输出：如果是单文件则默认写到同目录下 `*_denoise.wav`；
        如果是目录则默认输出到 `output_data/denoise_tool`
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))

from src.utils import gtcrn_denoise  # type: ignore

try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore

    def print_info(msg: str):
        print(info(msg))

    def print_warning(msg: str):
        print(warning(msg))

    def print_error(msg: str):
        print(error(msg))

    def print_success(msg: str):
        print(success(msg))

    def print_header(msg: str):
        print(header(msg))

except Exception:
    def print_info(msg: str):
        print(f"[INFO] {msg}")

    def print_warning(msg: str):
        print(f"[WARNING] {msg}")

    def print_error(msg: str):
        print(f"[ERROR] {msg}")

    def print_success(msg: str):
        print(f"[SUCCESS] {msg}")

    def print_header(msg: str):
        print(f"=== {msg} ===")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GTCRN 独立降噪工具（ONNX 优先）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 单文件：默认输出到同目录 xxx_denoise.wav
  python -m src.tools.gtcrn_denoise --input ./a.wav

  # 目录：默认输出到 output_data/denoise_tool
  python -m src.tools.gtcrn_denoise --input ./input_dir

  # 显式指定模型和输出
  python -m src.tools.gtcrn_denoise --input ./input_dir --model ./models/gtcrn/gtcrn.onnx --output ./out_dir

  # 如果是 torch 权重，可导出 ONNX
  python -m src.tools.gtcrn_denoise --input ./a.wav --model ./weights/model_trained_on_dns3.tar --export_dir ./models/gtcrn_onnx
        """,
    )
    parser.add_argument("--input", required=True, help="输入音频文件或目录")
    parser.add_argument(
        "--model",
        default=str(PROJECT_ROOT / "models" / "gtcrn" / "gtcrn.onnx"),
        help="GTCRN 模型路径，默认: models/gtcrn/gtcrn.onnx",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出 wav 文件或目录；单文件默认同目录 *_denoise.wav，目录默认 output_data/denoise_tool",
    )
    parser.add_argument(
        "--export_dir",
        default=None,
        help="若输入为 .tar/.pt/.pth，则导出 ONNX 的目录",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    model_path = Path(args.model).resolve()
    export_dir = Path(args.export_dir).resolve() if args.export_dir else None
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        if input_path.is_file():
            output_path = input_path.with_name(f"{input_path.stem}_denoise.wav")
        else:
            output_path = PROJECT_ROOT / "output_data" / "denoise_tool"

    print_header("GTCRN 独立降噪")
    print_info(f"输入: {input_path}")
    print_info(f"模型: {model_path}")
    print_info(f"输出: {output_path}")

    try:
        resolved_model = gtcrn_denoise._resolve_model(model_path, export_dir=export_dir)  # type: ignore[attr-defined]
        print_info(f"使用模型: {resolved_model}")
        denoiser = gtcrn_denoise.OnnxGtcrnDenoiser(resolved_model)  # type: ignore[attr-defined]
    except Exception as e:
        print_error(f"初始化失败: {e}")
        return 1

    files = gtcrn_denoise._find_audio_files(input_path)  # type: ignore[attr-defined]
    if not files:
        print_warning("未找到可处理的音频文件")
        return 0

    try:
        if input_path.is_file():
            if output_path.suffix.lower() != ".wav":
                output_path = output_path.with_suffix(".wav")
            gtcrn_denoise.process_one(files[0], output_path, denoiser)  # type: ignore[attr-defined]
            print_success(f"完成: {output_path}")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            for f in files:
                out_file = output_path / f"{f.stem}.wav"
                print_info(f"降噪: {f.name} -> {out_file.name}")
                gtcrn_denoise.process_one(f, out_file, denoiser)  # type: ignore[attr-defined]
            print_success(f"批量完成，输出目录: {output_path}")
    except Exception as e:
        print_error(f"处理失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

