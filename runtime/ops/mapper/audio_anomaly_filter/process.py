# -- encoding: utf-8 --

import math
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from datamate.core.base_op import Mapper

try:
    from .audio_skip import is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import is_audio_sample, mark_skipped_sample


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _audio_ext(sample: Dict[str, Any], default_ext: str = "wav") -> str:
    for key in ("target_type", "fileType"):
        ext = str(sample.get(key) or "").strip().lower().lstrip(".")
        if ext:
            return ext
    path_value = str(sample.get("filePath") or "").strip()
    suffix = Path(path_value).suffix.lower().lstrip(".") if path_value else ""
    return suffix or default_ext


def _source_audio_bytes(sample: Dict[str, Any], data_key: str, filepath_key: str, read_file: bool = False) -> bytes:
    data = sample.get(data_key)
    if isinstance(data, (bytes, bytearray)) and data:
        return bytes(data)
    if not read_file:
        return b""
    path = Path(str(sample.get(filepath_key) or "")).expanduser()
    if path.exists() and path.is_file():
        return path.read_bytes()
    return b""


def _safe_marker(value: str, default: str = "invalid_audio") -> str:
    marker = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or default)).strip("._-")
    return marker[:80] or default


def _strip_quality_marker(stem: str) -> str:
    return re.sub(r"__quality_invalid(?:_[A-Za-z0-9._-]+)?$", "", str(stem or "sample"))


def _mark_quality_filename(sample: Dict[str, Any], filename_key: str, reason: str, target_ext: str) -> None:
    file_name = str(sample.get(filename_key) or "").strip()
    stem = _strip_quality_marker(Path(file_name).stem if file_name else "sample")
    sample[filename_key] = f"{stem}__quality_invalid_{_safe_marker(reason)}.{target_ext}"


def _load_wave_mono(path: Path) -> Tuple[List[float], int]:
    try:
        import torchaudio  # type: ignore

        wav, sr = torchaudio.load(str(path))
        if wav.ndim > 1:
            wav = wav.mean(dim=0, keepdim=True)
        return wav.squeeze(0).float().tolist(), int(sr)
    except Exception:
        try:
            import soundfile as sf  # type: ignore

            data, sr = sf.read(str(path), always_2d=False)
            if getattr(data, "ndim", 1) > 1:
                data = data.mean(axis=1)
            return data.tolist(), int(sr)
        except Exception as e:
            raise RuntimeError(f"failed to read audio: {path}, error={e}") from e


def _load_source_mono(sample: Dict[str, Any], data_key: str, filepath_key: str) -> Tuple[List[float], int]:
    data = sample.get(data_key)
    if isinstance(data, (bytes, bytearray)) and data:
        with tempfile.NamedTemporaryFile(suffix=f".{_audio_ext(sample)}", delete=False) as tmp:
            tmp.write(bytes(data))
            tmp_path = Path(tmp.name)
        try:
            return _load_wave_mono(tmp_path)
        finally:
            try:
                tmp_path.unlink()
            except Exception:
                pass
    return _load_wave_mono(Path(str(sample.get(filepath_key) or "")).expanduser().resolve())


def _frame_rms(x: List[float], sr: int, frame_ms: float, hop_ms: float) -> Tuple[List[float], float]:
    if not x or sr <= 0:
        return [], 0.0
    frame_len = max(1, int(sr * frame_ms / 1000.0))
    hop = max(1, int(sr * hop_ms / 1000.0))
    total_sq = sum(float(v) * float(v) for v in x)
    global_rms = math.sqrt(total_sq / max(1, len(x)))
    rms_list: List[float] = []
    for start in range(0, len(x), hop):
        end = min(start + frame_len, len(x))
        if end <= start:
            continue
        frame = x[start:end]
        rms_list.append(math.sqrt(sum(float(v) * float(v) for v in frame) / max(1, len(frame))))
    return rms_list, global_rms


class AudioAnomalyFilter(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_dur = float(kwargs.get("minDur", 1.0))
        self.max_dur = float(kwargs.get("maxDur", 20000.0))
        self.silence_ratio_th = float(kwargs.get("silenceRatioTh", 0.8))
        self.silence_rms_ratio_th = float(kwargs.get("silenceRmsRatioTh", 0.05))
        self.skip_invalid_downstream = _as_bool(kwargs.get("skipInvalidDownstream", True))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        if not is_audio_sample(sample, self.filepath_key, self.filetype_key, self.target_type_key, self.data_key):
            return mark_skipped_sample(
                sample,
                "non_audio_or_reference_file",
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )

        audio_bytes_for_export = _source_audio_bytes(sample, self.data_key, self.filepath_key)
        path_value = str(sample.get(self.filepath_key) or "").strip()
        path_exists = bool(audio_bytes_for_export) or (bool(path_value) and Path(path_value).expanduser().exists())
        reasons: List[str] = []
        quality_flag = "ok"
        read_error = ""

        if not path_exists:
            duration = 0.0
            silence_ratio = 1.0
            global_rms = 0.0
            quality_flag = "invalid"
            read_error = f"FileNotFoundError: input audio does not exist: {sample.get(self.filepath_key)}"
            reasons.append("missing_audio_file")
        else:
            try:
                wav, sr = _load_source_mono(sample, self.data_key, self.filepath_key)
                duration = float(len(wav)) / float(sr) if sr > 0 else 0.0
                rms_frames, global_rms = _frame_rms(wav, sr, frame_ms=25.0, hop_ms=10.0)
                if not rms_frames or global_rms <= 0.0:
                    silence_ratio = 1.0
                else:
                    threshold = max(1e-8, global_rms * float(self.silence_rms_ratio_th))
                    silent = sum(1 for rms in rms_frames if rms < threshold)
                    silence_ratio = float(silent) / float(len(rms_frames))
            except Exception as e:
                duration = 0.0
                silence_ratio = 1.0
                global_rms = 0.0
                quality_flag = "invalid"
                read_error = f"{type(e).__name__}: {e}"
                reasons.append("unreadable_audio")

        if duration <= 0.0:
            quality_flag = "invalid"
            if "duration_le_zero" not in reasons:
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
            "read_error": read_error,
            "skip_downstream": self.skip_invalid_downstream,
        }
        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_quality"] = report
        sample[self.ext_params_key] = ext

        sample[self.text_key] = ""
        if self.is_last_op and not audio_bytes_for_export:
            audio_bytes_for_export = _source_audio_bytes(
                sample,
                self.data_key,
                self.filepath_key,
                read_file=True,
            )
        if audio_bytes_for_export:
            sample[self.data_key] = audio_bytes_for_export
        if self.is_last_op:
            target_ext = _audio_ext(sample)
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = target_ext
            if quality_flag == "invalid":
                _mark_quality_filename(sample, self.filename_key, report["reason"] or "invalid_audio", target_ext)

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAnomalyFilter costs {time.time() - start:6f} s"
        )
        return sample
