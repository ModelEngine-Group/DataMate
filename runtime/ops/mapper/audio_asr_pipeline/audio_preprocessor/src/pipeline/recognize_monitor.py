#!/usr/bin/env python3
"""
识别管理脚本（Python 版）

- 默认读取 output_data/split/item_with_lang.list
- 按 lang 将子片段拆分为中文/英文两份列表
- 先统一识别中文，再识别英文（减少模型切换开销）
- 调用 merge_asr_by_source 按 source_key/segment_index 合并回原音频文本
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 颜色打印工具
sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))
try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore

    def print_info(msg: str):
        print(info(msg))

    def print_warning(msg: str):
        print(warning(msg))

    def print_error(msg: str):
        print(error(msg))

    def print_ok(msg: str):
        print(ok(msg))

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

    def print_ok(msg: str):
        print(f"[OK] {msg}")

    def print_success(msg: str):
        print(f"[SUCCESS] {msg}")

    def print_header(msg: str):
        print(f"=== {msg} ===")


# YAML 配置加载（可选）
try:
    from yaml_config_loader import parse_args_with_yaml_config  # type: ignore
except Exception:
    parse_args_with_yaml_config = None  # type: ignore[assignment]


def split_by_lang(list_file: Path, tmp_dir: Path) -> Tuple[Path, Path, int, int]:
    """根据 lang 字段将 item_with_lang.list 拆成 zh/en 两个 jsonl 列表。"""
    zh_list = tmp_dir / "zh.list"
    en_list = tmp_dir / "en.list"

    zh_items: List[Dict] = []
    en_items: List[Dict] = []

    with list_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            row = {
                "key": d.get("key", ""),
                "wav": d.get("wav", ""),
                "txt": d.get("txt", ""),
            }
            if d.get("lang") == "zh":
                zh_items.append(row)
            else:
                en_items.append(row)

    for path, items in [(zh_list, zh_items), (en_list, en_items)]:
        with path.open("w", encoding="utf-8") as f:
            for r in items:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print_info(f"zh segments: {len(zh_items)} en segments: {len(en_items)}")
    return zh_list, en_list, len(zh_items), len(en_items)


def _find_audio_files(input_path: Path) -> List[Path]:
    exts = {".wav", ".flac", ".mp3", ".aac", ".m4a", ".ogg", ".webm"}
    if input_path.is_file():
        return [input_path]
    files: List[Path] = []
    for p in input_path.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return sorted(files)


def run_recognize(language: str, audio_list: Path, result_dir: Path, device: str) -> int:
    """通过子进程调用 src.utils.recognize."""
    import subprocess

    cmd = [
        sys.executable,
        "-m",
        "src.utils.recognize",
        "--language",
        language,
        "--audio_list",
        str(audio_list),
        "--result_dir",
        str(result_dir),
    ]
    if device:
        cmd.extend(["--device", device])

    # 确保在项目根目录下运行，从而可以找到 src 包
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT))


def _run_recognize_thread(
    language: str,
    audio_list: Path,
    result_dir: Path,
    device: str,
    rc_out: Dict[str, int],
) -> None:
    rc_out[language] = int(run_recognize(language, audio_list, result_dir, device=device))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="识别管理脚本：读取 split 清单，按 zh/en 分别识别并合并结果",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 recognize_monitor: {split_dir:..., asr_root:...} 或直接顶层同名键",
    )
    parser.add_argument(
        "--split_dir",
        default=str(PROJECT_ROOT / "output_data" / "split"),
        help="split 输出目录（包含 item_with_lang.list），默认: output_data/split",
    )
    parser.add_argument(
        "--list_file",
        default=None,
        help="自定义清单路径（默认使用 split_dir/item_with_lang.list）",
    )
    parser.add_argument(
        "--asr_root",
        default=str(PROJECT_ROOT / "output_data" / "asr"),
        help="ASR 结果根目录，默认: output_data/asr",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help=argparse.SUPPRESS,
    )
    # 默认并行，同时保留 --no-parallel 以便资源不足时回退
    parser.add_argument(
        "--parallel",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="是否并行运行中/英两路识别以提速（默认开启；资源不足可用 --no-parallel 关闭）",
    )
    parser.add_argument(
        "--from_denoise",
        action="store_true",
        help="若未提供清单，默认从 output_data/denoise 扫描音频并生成临时 list",
    )
    if parse_args_with_yaml_config:
        args = parse_args_with_yaml_config(
            parser,
            section="recognize_monitor",
            default_config_paths=[PROJECT_ROOT / "config" / "recognize_monitor.yaml"],
        )
    else:
        args = parser.parse_args()

    split_dir = Path(args.split_dir).resolve()
    asr_root = Path(args.asr_root).resolve()
    list_file = Path(args.list_file).resolve() if args.list_file else split_dir / "item_with_lang.list"

    print_header("识别管理")
    print_info(f"项目根: {PROJECT_ROOT}")
    print_info(f"清单: {list_file}")
    print_info(f"ASR 输出: {asr_root}")

    if not list_file.exists():
        if args.from_denoise:
            denoise_dir = PROJECT_ROOT / "output_data" / "denoise"
            print_warning(f"清单不存在，改为从目录扫描: {denoise_dir}")
            audio_files = _find_audio_files(denoise_dir)
            if not audio_files:
                print_error("未找到可识别的音频")
                return 1
            tmp_list = Path(tempfile.mkdtemp(prefix="hz_list_")) / "item_with_lang.list"
            tmp_list.parent.mkdir(parents=True, exist_ok=True)
            with tmp_list.open("w", encoding="utf-8") as f:
                for p in audio_files:
                    row = {"key": p.stem, "wav": str(p.resolve()), "txt": "", "lang": "en"}
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            list_file = tmp_list
        else:
            print_error(f"清单不存在: {list_file}")
            print_info("请先运行: python -m src.pipeline.3_split_and_tag 或传 --from_denoise")
            return 1

    tmp_dir = Path(tempfile.mkdtemp(prefix="hz_split_"))
    try:
        zh_list, en_list, zh_n, en_n = split_by_lang(list_file, tmp_dir)

        # 识别：默认并行（可用 --no-parallel 关闭）
        (asr_root / "zh").mkdir(parents=True, exist_ok=True)
        (asr_root / "en").mkdir(parents=True, exist_ok=True)

        if args.parallel and zh_n > 0 and en_n > 0:
            print_info("并行识别：同时启动中文与英文片段识别...")
            rc_out: Dict[str, int] = {}
            t_zh = threading.Thread(
                target=_run_recognize_thread,
                args=("zh", zh_list, asr_root / "zh", args.device, rc_out),
                daemon=False,
            )
            t_en = threading.Thread(
                target=_run_recognize_thread,
                args=("en", en_list, asr_root / "en", args.device, rc_out),
                daemon=False,
            )
            t_zh.start()
            t_en.start()
            t_zh.join()
            t_en.join()

            zh_rc = int(rc_out.get("zh", 1))
            en_rc = int(rc_out.get("en", 1))
            if zh_rc != 0:
                print_error(f"中文识别失败，返回码: {zh_rc}")
                return zh_rc
            if en_rc != 0:
                print_error(f"英文识别失败，返回码: {en_rc}")
                return en_rc
        else:
            if zh_n > 0:
                print_info("识别中文片段...")
                rc = run_recognize("zh", zh_list, asr_root / "zh", device=args.device)
                if rc != 0:
                    print_error(f"中文识别失败，返回码: {rc}")
                    return rc

            if en_n > 0:
                print_info("识别英文片段...")
                rc = run_recognize("en", en_list, asr_root / "en", device=args.device)
                if rc != 0:
                    print_error(f"英文识别失败，返回码: {rc}")
                    return rc

        # 合并结果
        print_info("合并子片段结果...")
        from src.pipeline import merge_asr_by_source  # type: ignore

        rc = merge_asr_by_source.main_for_api(  # type: ignore[attr-defined]
            list_file=list_file,
            zh_text=asr_root / "zh" / "ctc_greedy_search" / "text",
            en_text=asr_root / "en" / "ctc_greedy_search" / "text",
            output=asr_root / "merged_text.txt",
        )
        if rc != 0:
            print_error(f"合并失败，返回码: {rc}")
            return rc

        print_success(f"完成。合并文本: {asr_root / 'merged_text.txt'}")
        return 0
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
