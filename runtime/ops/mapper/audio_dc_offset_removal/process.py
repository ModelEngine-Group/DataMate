# -- encoding: utf-8 --

import io
import time
from pathlib import Path
from typing import Dict, Any, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


AUDIO_EXTS = {
    "aac",
    "aif",
    "aiff",
    "amr",
    "au",
    "flac",
    "m4a",
    "mp3",
    "oga",
    "ogg",
    "opus",
    "snd",
    "wav",
    "webm",
    "wma",
}


def _sample_path(sample: Dict[str, Any], filepath_key: str) -> Path:
    return Path(str(sample.get(filepath_key, "")).strip()).expanduser()


def _path_ext(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return Path(text).suffix.lower().lstrip(".")


def _sample_ext(
    sample: Dict[str, Any],
    filepath_key: str,
    filetype_key: str,
    target_type_key: str,
) -> str:
    for key in (target_type_key, filetype_key):
        value = str(sample.get(key) or "").strip().lower().lstrip(".")
        if value:
            return value
    return _sample_path(sample, filepath_key).suffix.lower().lstrip(".")


def _is_reference_value(value: object) -> bool:
    try:
        parts = {part.lower() for part in Path(str(value or "")).parts}
        return "references" in parts or "reference" in parts
    except Exception:
        return False


def _source_skip_reason(sample: Dict[str, Any], filepath_key: str, filetype_key: str, target_type_key: str, data_key: str) -> str:
    for key in (filepath_key, "sourceFilePath", "fileName", "sourceFileName"):
        value = sample.get(key)
        if _is_reference_value(value):
            return "non_audio_or_reference_file"

    for key in (filepath_key, "sourceFilePath", "fileName", "sourceFileName"):
        ext = _path_ext(sample.get(key))
        if ext and ext not in AUDIO_EXTS:
            return "non_audio_or_reference_file"

    data = sample.get(data_key)
    if isinstance(data, (bytes, bytearray)) and data:
        return ""

    if _sample_ext(sample, filepath_key, filetype_key, target_type_key) not in AUDIO_EXTS:
        return "non_audio_or_reference_file"
    return ""


def _load_audio(source: object) -> Tuple["object", int]:
    import soundfile as sf  # type: ignore

    if isinstance(source, (bytes, bytearray)):
        data, sr = sf.read(io.BytesIO(bytes(source)), always_2d=False)
    else:
        data, sr = sf.read(str(source), always_2d=False)
    return data, int(sr)


def _dump_audio(data: "object", sr: int, fmt: str) -> bytes:
    try:
        import soundfile as sf  # type: ignore

        with io.BytesIO() as buf:
            sf.write(buf, data, int(sr), format=fmt.upper() if fmt else "WAV")
            return buf.getvalue()
    except Exception as e:
        raise RuntimeError(f"编码音频失败（需要 soundfile，fmt={fmt}）: {e}") from e


class AudioDcOffsetRemoval(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_mode = str(kwargs.get("channelMode", "preserve")).strip().lower()
        self.offset_threshold = float(kwargs.get("offsetThreshold", 0.0))
        self.out_format = "wav"

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        quality_skip_reason = invalid_quality_reason(sample, self.ext_params_key)
        if quality_skip_reason:
            return mark_skipped_sample(
                sample,
                quality_skip_reason,
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )

        skip_reason = _source_skip_reason(
            sample,
            self.filepath_key,
            self.filetype_key,
            self.target_type_key,
            self.data_key,
        )
        if skip_reason:
            return mark_skipped_sample(
                sample,
                skip_reason,
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )
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

        in_path = Path(sample.get(self.filepath_key, "")).resolve()
        source = sample.get(self.data_key) or in_path
        if not isinstance(source, (bytes, bytearray)) and not in_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {in_path}")

        try:
            data, sr = _load_audio(source)
        except Exception as e:
            return mark_skipped_sample(
                sample,
                f"unreadable_audio:{type(e).__name__}",
                self.__class__.__name__,
                self.text_key,
                self.data_key,
                self.filetype_key,
                self.target_type_key,
                self.ext_params_key,
            )

        try:
            import numpy as np

            x = np.asarray(data, dtype=np.float32)
            if self.channel_mode == "mono" and x.ndim > 1:
                x = x.mean(axis=1)
            elif self.channel_mode not in {"preserve", "mono"}:
                raise ValueError(f"不支持的声道处理方式: {self.channel_mode}")

            if x.size:
                if x.ndim == 1:
                    offsets = np.array([float(np.mean(x))], dtype=np.float32)
                else:
                    offsets = np.mean(x, axis=0).astype(np.float32)
                max_abs_offset = float(np.max(np.abs(offsets)))
                if max_abs_offset >= max(0.0, float(self.offset_threshold)):
                    y = x - offsets
                    applied = True
                else:
                    y = x
                    applied = False
            else:
                offsets = np.array([], dtype=np.float32)
                max_abs_offset = 0.0
                y = x
                applied = False
        except Exception as e:
            raise RuntimeError(f"处理失败（需要 numpy）: {e}") from e

        sample[self.data_key] = _dump_audio(y, sr, self.out_format)
        sample[self.text_key] = ""
        sample[self.target_type_key] = self.out_format
        sample[self.filetype_key] = "txt" if self.is_last_op else self.out_format
        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_dc_offset_removal"] = {
            "output_format": self.out_format,
            "channel_mode": self.channel_mode,
            "offset_threshold": self.offset_threshold,
            "max_abs_offset": max_abs_offset,
            "applied": applied,
            "sample_rate": sr,
        }
        sample[self.ext_params_key] = ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioDcOffsetRemoval costs {time.time() - start:6f} s"
        )
        return sample
