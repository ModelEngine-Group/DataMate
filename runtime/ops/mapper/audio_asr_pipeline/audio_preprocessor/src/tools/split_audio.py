#!/usr/bin/env python3
"""
切分音频小工具：将长音频按指定时长切分为多个片段并导出为 wav。
不处理 list 文件，仅做目录/文件切分。
"""

import argparse
import sys
from pathlib import Path
from typing import List

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
try:
    from pydub import AudioSegment  # type: ignore
except ImportError:
    AudioSegment = None


def split_one(
    wav_path: Path,
    output_dir: Path,
    max_seconds: int,
    base_name: str,
) -> int:
    """将单个文件切分，返回生成的片段数。"""
    if AudioSegment is None:
        raise RuntimeError("请在 DataMate 运行环境安装 pydub")
    audio = AudioSegment.from_file(str(wav_path))
    duration_ms = len(audio)
    segment_ms = max(1, max_seconds) * 1000
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    start_ms = 0
    while start_ms < duration_ms:
        end_ms = min(start_ms + segment_ms, duration_ms)
        chunk = audio[start_ms:end_ms]
        out_path = output_dir / f"{base_name}_part{count}.wav"
        chunk.export(str(out_path), format="wav")
        count += 1
        start_ms = end_ms
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="按指定时长切分音频为多个 wav 片段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="输入音频文件或目录（目录则处理其中所有 wav）",
    )
    parser.add_argument(
        "--output_dir", "-o",
        required=True,
        help="输出目录",
    )
    parser.add_argument(
        "--max_seconds", "-s",
        type=int,
        default=120,
        help="每段最大秒数，默认 120",
    )
    args = parser.parse_args()

    if not args.input:
        parser.error("请指定输入文件或目录")
    if AudioSegment is None:
        print("[ERROR] 无法导入 pydub", file=sys.stderr)
        return 1

    inp = Path(args.input).resolve()
    out_dir = Path(args.output_dir).resolve()
    if not inp.exists():
        print(f"[ERROR] 不存在: {inp}", file=sys.stderr)
        return 1

    files: List[Path] = []
    if inp.is_file():
        if inp.suffix.lower() not in (".wav", ".mp3", ".flac", ".m4a", ".aac"):
            print("[WARNING] 非常见音频格式，尝试继续", file=sys.stderr)
        files.append(inp)
    else:
        for ext in ("*.wav", "*.WAV", "*.mp3", "*.flac", "*.m4a", "*.aac"):
            files.extend(inp.rglob(ext))
        files = sorted(set(files))

    if not files:
        print("[WARNING] 未找到音频文件", file=sys.stderr)
        return 0

    total = 0
    for f in files:
        base = f.stem
        n = split_one(f, out_dir, args.max_seconds, base)
        total += n
        print(f"[INFO] {f.name} -> {n} 段")
    print(f"[OK] 共生成 {total} 个片段 -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
