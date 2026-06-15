#!/usr/bin/env python3
"""
将归一化后的音频按不超过 2 分钟切分为子片段，并处理 item_with_lang.list。
在输出目录生成新的 list 文件，记录原音频与子片段的对应关系及语言标签。
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# 项目根与路径
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts" / "audio_convert"))
sys.path.insert(0, str(_PROJECT_ROOT / "src" / "utils"))

try:
    from color_utils import info, warning, error, ok, success, header
except ImportError:
    def info(msg): return f"[INFO] {msg}"
    def warning(msg): return f"[WARNING] {msg}"
    def error(msg): return f"[ERROR] {msg}"
    def ok(msg): return f"[OK] {msg}"
    def success(msg): return f"[SUCCESS] {msg}"
    def header(msg): return f"=== {msg} ==="

def _print_info(msg): print(info(msg))
def _print_warning(msg): print(warning(msg))
def _print_error(msg): print(error(msg))
def _print_ok(msg): print(ok(msg))
def _print_success(msg): print(success(msg))
def _print_header(msg): print(header(msg))

# YAML 配置加载（可选）
try:
    from yaml_config_loader import parse_args_with_yaml_config  # type: ignore
except Exception:
    parse_args_with_yaml_config = None  # type: ignore[assignment]

DEFAULT_INPUT_DIR = _PROJECT_ROOT / "output_data" / "denoise"
DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "output_data" / "split"
DEFAULT_LIST_PATH = _PROJECT_ROOT / "output_data" / "lid" / "item_with_lang.list"
MAX_SEGMENT_SECONDS = 120  # 2 分钟


def _load_item_list(path: Path) -> List[Dict]:
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _find_audio_files(input_path: Path) -> List[Path]:
    exts = {".wav", ".flac", ".mp3", ".aac", ".m4a", ".ogg", ".webm"}
    if input_path.is_file():
        return [input_path]
    files: List[Path] = []
    for p in input_path.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return sorted(files)


def _import_pydub():
    try:
        from pydub import AudioSegment  # type: ignore
        return AudioSegment
    except Exception as e:
        raise RuntimeError(f"无法导入 pydub，请在 DataMate 运行环境安装 pydub: {e}") from e


def split_audio_to_segments(
    wav_path: Path,
    output_dir: Path,
    base_key: str,
    lang: str,
    max_seconds: int = MAX_SEGMENT_SECONDS,
) -> List[Dict]:
    """
    将单个 wav 按 max_seconds 切分，导出到 output_dir，返回子片段 list 项。
    每项含 key, wav, txt, lang, source_key, segment_index。
    """
    AudioSegment = _import_pydub()
    audio = AudioSegment.from_file(str(wav_path))
    duration_ms = len(audio)
    segment_ms = max_seconds * 1000
    if segment_ms <= 0:
        segment_ms = duration_ms

    out_items = []
    seg_idx = 0
    start_ms = 0
    while start_ms < duration_ms:
        end_ms = min(start_ms + segment_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        part_key = f"{base_key}_part{seg_idx}"
        out_wav = output_dir / f"{part_key}.wav"
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        chunk.export(str(out_wav), format="wav")
        out_items.append({
            "key": part_key,
            "wav": str(out_wav.resolve()),
            "txt": "",
            "lang": lang,
            "source_key": base_key,
            "segment_index": seg_idx,
        })
        start_ms = end_ms
        seg_idx += 1
    return out_items


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将音频切分为不超过 2 分钟的子片段，并生成带语言与对应关系的 list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 split_and_tag: {input_dir:..., max_seconds:...} 或直接顶层同名键",
    )
    parser.add_argument(
        "--input_dir", "-i",
        default=str(DEFAULT_INPUT_DIR),
        help=f"音频输入目录，默认: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output_dir", "-o",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"子片段输出目录，默认: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--list_file", "-l",
        default=str(DEFAULT_LIST_PATH),
        help=f"带语言的 list 文件 (jsonl)，默认: {DEFAULT_LIST_PATH}",
    )
    parser.add_argument(
        "--from_list",
        action="store_true",
        help="输入作为 list 文件处理；默认按目录扫描音频",
    )
    parser.add_argument(
        "--max_seconds", "-s",
        type=int,
        default=MAX_SEGMENT_SECONDS,
        help=f"每段最大秒数，默认: {MAX_SEGMENT_SECONDS}",
    )
    if parse_args_with_yaml_config:
        args = parse_args_with_yaml_config(
            parser,
            section="split_and_tag",
            default_config_paths=[_PROJECT_ROOT / "config" / "split_and_tag.yaml"],
        )
    else:
        args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    list_path = Path(args.list_file).resolve()

    _print_header("切分音频并打标签")

    items: List[Dict] = []
    if args.from_list or list_path.exists():
        if not list_path.exists():
            _print_error(f"列表文件不存在: {list_path}")
            return 1
        items = _load_item_list(list_path)
    else:
        if not input_dir.exists():
            _print_error(f"输入目录不存在: {input_dir}")
            return 1
        audio_files = _find_audio_files(input_dir)
        if not audio_files:
            _print_warning("未找到任何音频文件")
            return 0
        items = [{"key": p.stem, "wav": str(p.resolve()), "txt": "", "lang": "en"} for p in audio_files]

    if not items:
        _print_warning("输入为空，退出")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    all_segments: List[Dict] = []
    for it in items:
        key = it.get("key", "")
        wav = it.get("wav") or it.get("audio") or it.get("path", "")
        lang = it.get("lang", "en")
        if not wav or not key:
            _print_warning(f"跳过无效项: key={key}, wav={wav}")
            continue
        wav_path = Path(wav)
        if not wav_path.exists():
            _print_warning(f"文件不存在，跳过: {wav_path}")
            continue
        try:
            segs = split_audio_to_segments(
                wav_path, output_dir, key, lang,
                max_seconds=args.max_seconds,
            )
            all_segments.extend(segs)
        except Exception as e:
            _print_error(f"切分失败 {wav_path}: {e}")
            continue

    out_list_path = output_dir / "item_with_lang.list"
    with open(out_list_path, "w", encoding="utf-8") as f:
        for it in all_segments:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    _print_success(f"完成。共 {len(all_segments)} 个子片段，列表: {out_list_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
