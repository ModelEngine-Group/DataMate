# -- encoding: utf-8 --

import math
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

from loguru import logger

from datamate.core.base_op import Mapper


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in {"1", "true", "yes", "y", "on"}


def _load_wave_mono(path: Path) -> Tuple[List[float], int]:
    """
    尽量少依赖：优先 torchaudio，其次 soundfile。
    返回 mono waveform(list[float]) 与采样率。
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
            if getattr(data, "ndim", 1) > 1:
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
    total_sq = 0.0
    for v in x:
        total_sq += float(v) * float(v)
    global_rms = math.sqrt(total_sq / max(1, n))
    rms_list: List[float] = []
    for start in range(0, n, hop):
        end = min(start + frame_len, n)
        if end <= start:
            continue
        s = 0.0
        cnt = 0
        for v in x[start:end]:
            s += float(v) * float(v)
            cnt += 1
        rms_list.append(math.sqrt(s / cnt) if cnt else 0.0)
    return rms_list, global_rms


class AudioAnomalyFilter(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_dur = float(kwargs.get("minDur", 1.0))
        self.max_dur = float(kwargs.get("maxDur", 20000.0))
        self.silence_ratio_th = float(kwargs.get("silenceRatioTh", 0.8))
        self.silence_rms_ratio_th = float(kwargs.get("silenceRmsRatioTh", 0.05))
        self.keep_invalid = _as_bool(kwargs.get("keepInvalid", False))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        wav_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not wav_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {wav_path}")

        wav, sr = _load_wave_mono(wav_path)
        n = len(wav)
        duration = float(n) / float(sr) if sr > 0 else 0.0
        rms_frames, global_rms = _frame_rms(wav, sr, frame_ms=25.0, hop_ms=10.0)
        if not rms_frames or global_rms <= 0.0:
            silence_ratio = 1.0
        else:
            th = max(1e-8, global_rms * float(self.silence_rms_ratio_th))
            silent = sum(1 for r in rms_frames if r < th)
            silence_ratio = float(silent) / float(len(rms_frames))

        reasons: List[str] = []
        quality_flag = "ok"
        if duration <= 0.0:
            quality_flag = "invalid"
            reasons.append("duration_le_zero")
        elif duration < self.min_dur:
            quality_flag = "invalid"
            reasons.append("too_short")
        elif duration > self.max_dur:
            quality_flag = "invalid"
            reasons.append("too_long")
        if silence_ratio >= self.silence_ratio_th:
            quality_flag = "invalid"
            reasons.append("too_much_silence")

        report = {
            "quality_flag": quality_flag,
            "duration": round(duration, 3),
            "silence_ratio": round(silence_ratio, 4),
            "global_rms": round(global_rms, 6),
            "reason": ",".join(reasons) if reasons else "",
        }
        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_quality"] = report
        sample[self.ext_params_key] = ext

        if quality_flag == "invalid" and not self.keep_invalid:
            # 清空内容以便后续被框架过滤（Mapper 的“空内容过滤”逻辑）
            sample[self.text_key] = ""
            sample[self.data_key] = b""
        else:
            if not sample.get(self.text_key):
                sample[self.text_key] = "ok"
            sample[self.data_key] = b""

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAnomalyFilter costs {time.time() - start:6f} s"
        )
        return sample

