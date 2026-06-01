#!/usr/bin/env python3
"""
音频异常检测与过滤

设计目标：
- 作为 normalization 之后、LID 之前的质量过滤步骤
- 默认扫描 output_data/normalization 目录中的音频
- 对每个音频计算：
  - 时长（秒）
  - 静音帧比例（基于短时能量）
- 根据阈值打标 quality_flag，并输出 jsonl 列表

quality_flag 约定：
- "ok"       : 通过所有检查
- "invalid"  : 明显异常（时长不在范围或几乎全是静音）
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _project_root() -> Path:
    return Path(__file__).parent.parent.parent


def _ensure_utils_on_path() -> None:
    root = _project_root()
    utils_dir = root / "src" / "utils"
    scripts_dir = root / "scripts" / "audio_convert"
    for p in (utils_dir, scripts_dir):
        if p.exists():
            sp = str(p)
            if sp not in sys.path:
                sys.path.insert(0, sp)


_ensure_utils_on_path()

try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore
except Exception:  # pragma: no cover - 兼容无 color_utils 场景
    def info(msg: str) -> str:
        return f"[INFO] {msg}"

    def warning(msg: str) -> str:
        return f"[WARNING] {msg}"

    def error(msg: str) -> str:
        return f"[ERROR] {msg}"

    def ok(msg: str) -> str:
        return f"[OK] {msg}"

    def success(msg: str) -> str:
        return f"[SUCCESS] {msg}"

    def header(msg: str) -> str:
        return f"=== {msg} ==="


def _print_info(msg: str) -> None:
    print(info(msg))


def _print_warning(msg: str) -> None:
    print(warning(msg))


def _print_error(msg: str) -> None:
    print(error(msg))


def _print_success(msg: str) -> None:
    print(success(msg))


# YAML 配置加载（可选）
try:
    from yaml_config_loader import parse_args_with_yaml_config  # type: ignore
except Exception:
    parse_args_with_yaml_config = None  # type: ignore[assignment]


def _find_audio_files(audio_dir: Path) -> List[Path]:
    patterns = ["*.wav", "*.WAV", "*.flac", "*.FLAC", "*.mp3", "*.MP3", "*.aac", "*.AAC", "*.m4a", "*.M4A"]
    files: List[Path] = []
    for pat in patterns:
        files.extend(audio_dir.rglob(pat))
    return sorted(set(files))


def _load_wave(path: Path) -> Tuple[List[float], int]:
    """
    读取音频为 mono waveform 和采样率。

    优先使用 torchaudio（项目已依赖 speechbrain，通常可用），
    若导入失败则退化为 soundfile; 再失败则抛错。
    """
    try:
        import torchaudio  # type: ignore

        wav, sr = torchaudio.load(str(path))
        if wav.ndim > 1:
            wav = wav.mean(dim=0, keepdim=True)
        mono = wav.squeeze(0).float().tolist()
        return mono, int(sr)
    except Exception:
        try:
            import soundfile as sf  # type: ignore

            data, sr = sf.read(str(path), always_2d=False)
            if data.ndim > 1:
                # stereo -> mono
                data = data.mean(axis=1)
            return data.tolist(), int(sr)
        except Exception as e:
            raise RuntimeError(f"读取音频失败: {path}, error={e}") from e


def _frame_rms(x: List[float], sr: int, frame_ms: float, hop_ms: float) -> Tuple[List[float], float]:
    if not x or sr <= 0:
        return [], 0.0
    frame_len = max(1, int(sr * frame_ms / 1000.0))
    hop = max(1, int(sr * hop_ms / 1000.0))
    n = len(x)
    rms_list: List[float] = []
    total_sq = 0.0
    for v in x:
        total_sq += float(v) * float(v)
    global_rms = math.sqrt(total_sq / max(1, n))
    for start in range(0, n, hop):
        end = min(start + frame_len, n)
        if end <= start:
            continue
        s = 0.0
        cnt = 0
        for v in x[start:end]:
            s += float(v) * float(v)
            cnt += 1
        if cnt == 0:
            rms = 0.0
        else:
            rms = math.sqrt(s / cnt)
        rms_list.append(rms)
    return rms_list, global_rms


def _analyze_one(
    path: Path,
    min_dur: float,
    max_dur: float,
    silence_ratio_th: float,
    silence_rms_ratio_th: float,
) -> Dict:
    wav, sr = _load_wave(path)
    n = len(wav)
    duration = float(n) / float(sr) if sr > 0 else 0.0

    rms_frames, global_rms = _frame_rms(wav, sr, frame_ms=25.0, hop_ms=10.0)
    if not rms_frames or global_rms <= 0.0:
        silence_ratio = 1.0
    else:
        th = max(1e-8, global_rms * silence_rms_ratio_th)
        silent = sum(1 for r in rms_frames if r < th)
        silence_ratio = float(silent) / float(len(rms_frames))

    reasons: List[str] = []
    quality_flag = "ok"

    if duration <= 0.0:
        quality_flag = "invalid"
        reasons.append("duration_le_zero")
    elif duration < min_dur:
        quality_flag = "invalid"
        reasons.append("too_short")
    elif duration > max_dur:
        quality_flag = "invalid"
        reasons.append("too_long")

    if silence_ratio >= silence_ratio_th:
        quality_flag = "invalid"
        reasons.append("too_much_silence")

    key = path.stem
    return {
        "key": key,
        "wav": str(path.resolve()),
        "duration": round(duration, 3),
        "silence_ratio": round(silence_ratio, 4),
        "global_rms": round(global_rms, 6),
        "quality_flag": quality_flag,
        "reason": ",".join(reasons) if reasons else "",
    }


def _dump_jsonl(path: Path, items: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")


def parse_arguments() -> argparse.Namespace:
    root = _project_root()
    default_audio_dir = root / "output_data" / "denoise"
    default_output = root / "output_data" / "denoise" / "item_with_quality.list"

    parser = argparse.ArgumentParser(
        description="音频异常检测与过滤（基于时长和静音比例的快速规则）",
    )
    parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="YAML 配置文件路径（可选）。支持写 anomaly_filter: {min_dur:..., silence_ratio_th:...} 或直接顶层同名键",
    )
    parser.add_argument(
        "--audio_dir",
        "-a",
        default=str(default_audio_dir),
        help=f"要扫描的音频目录，默认: {default_audio_dir}",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=str(default_output),
        help=f"输出 jsonl 列表路径，默认: {default_output}",
    )
    parser.add_argument(
        "--min_dur",
        type=float,
        default=1.0,
        help="最小时长（秒），小于该值视为异常，默认 1.0",
    )
    parser.add_argument(
        "--max_dur",
        type=float,
        default=20000.0,
        help="最大时长（秒），大于该值视为异常",
    )
    parser.add_argument(
        "--silence_ratio_th",
        type=float,
        default=0.8,
        help="静音帧比例阈值，超过则视为异常，默认 0.8",
    )
    parser.add_argument(
        "--silence_rms_ratio_th",
        type=float,
        default=0.05,
        help="静音判定阈值 = global_rms * 该比例，默认 0.05",
    )
    if parse_args_with_yaml_config:
        return parse_args_with_yaml_config(
            parser,
            section="anomaly_filter",
            default_config_paths=[root / "config" / "anomaly_filter.yaml"],
        )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    audio_dir = Path(args.audio_dir).resolve()
    output_path = Path(args.output).resolve()

    print(header("音频异常检测与过滤"))
    if not audio_dir.exists():
        _print_error(f"音频目录不存在: {audio_dir}")
        return 1

    files = _find_audio_files(audio_dir)
    if not files:
        _print_warning(f"目录中未找到任何音频文件: {audio_dir}")
        return 0

    _print_info(f"待分析音频数: {len(files)}")
    _print_info(
        f"参数: min_dur={args.min_dur}s, max_dur={args.max_dur}s, "
        f"silence_ratio_th={args.silence_ratio_th}, silence_rms_ratio_th={args.silence_rms_ratio_th}"
    )

    items: List[Dict] = []
    invalid_count = 0
    for idx, p in enumerate(files, start=1):
        try:
            it = _analyze_one(
                path=p,
                min_dur=float(args.min_dur),
                max_dur=float(args.max_dur),
                silence_ratio_th=float(args.silence_ratio_th),
                silence_rms_ratio_th=float(args.silence_rms_ratio_th),
            )
        except Exception as e:
            _print_warning(f"处理失败，标记为 invalid: {p}, error={e}")
            it = {
                "key": p.stem,
                "wav": str(p.resolve()),
                "duration": 0.0,
                "silence_ratio": 1.0,
                "global_rms": 0.0,
                "quality_flag": "invalid",
                "reason": "load_error",
            }
        if it.get("quality_flag") == "invalid":
            invalid_count += 1
        items.append(it)

        if idx % 20 == 0 or idx == len(files):
            _print_info(f"进度: {idx}/{len(files)}")

    _dump_jsonl(output_path, items)
    _print_success(f"分析完成，输出: {output_path}")
    _print_info(f"统计: 总数={len(items)}, invalid={invalid_count}, ok={len(items) - invalid_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

