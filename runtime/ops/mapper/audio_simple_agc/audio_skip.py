# -- encoding: utf-8 --

from pathlib import Path
from typing import Any, Dict

from loguru import logger


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

KNOWN_AUDIO_EXT_PARAM_KEYS = {
    "audio_format_convert",
    "audio_dc_offset_removal",
    "audio_gtcrn_denoise",
    "audio_trim_silence_edges",
    "audio_pre_emphasis",
    "audio_noise_gate",
    "audio_hum_notch",
    "audio_quantize_encode",
    "audio_rms_loudness_normalize",
    "audio_simple_agc",
    "audio_soft_peak_limiter",
    "audio_telephony_bandpass",
    "audio_lid",
}


def _parts(path_value: str) -> set[str]:
    try:
        return {part.lower() for part in Path(path_value).parts}
    except Exception:
        return set()


def is_reference_sample(sample: Dict[str, Any], filepath_key: str = "filePath") -> bool:
    path_value = str(sample.get(filepath_key) or "")
    return "references" in _parts(path_value)


def _ext_from_sample(
    sample: Dict[str, Any],
    filepath_key: str = "filePath",
    filetype_key: str = "fileType",
    target_type_key: str = "target_type",
) -> str:
    for key in (target_type_key, filetype_key):
        value = str(sample.get(key) or "").strip().lower().lstrip(".")
        if value:
            return value
    path_value = str(sample.get(filepath_key) or "").strip()
    return Path(path_value).suffix.lower().lstrip(".") if path_value else ""


def _path_looks_audio(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    return Path(text).suffix.lower().lstrip(".") in AUDIO_EXTS


def _has_audio_path_hint(sample: Dict[str, Any]) -> bool:
    for key in ("audio_path", "audioPath", "sourceAudioPath"):
        if _path_looks_audio(sample.get(key)):
            return True
    audios = sample.get("audios")
    if isinstance(audios, (list, tuple)):
        for item in audios:
            if _path_looks_audio(item):
                return True
    return False


def _has_audio_ext_params_hint(sample: Dict[str, Any], ext_params_key: str = "ext_params") -> bool:
    ext = sample.get(ext_params_key, {})
    if not isinstance(ext, dict):
        return False
    if any(key in ext for key in KNOWN_AUDIO_EXT_PARAM_KEYS):
        return True
    audio_skip = ext.get("audio_skip")
    if isinstance(audio_skip, dict) and any(key in audio_skip for key in KNOWN_AUDIO_EXT_PARAM_KEYS):
        return True
    return False


def resolve_audio_input_path(sample: Dict[str, Any], filepath_key: str = "filePath") -> Path:
    candidates = [
        sample.get("audio_path"),
        sample.get("audioPath"),
        sample.get("sourceAudioPath"),
    ]
    audios = sample.get("audios")
    if isinstance(audios, (list, tuple)):
        candidates.extend(audios)
    candidates.append(sample.get(filepath_key))

    for value in candidates:
        text = str(value or "").strip()
        if not text:
            continue
        path = Path(text).expanduser()
        if path.exists():
            return path.resolve()

    fallback = str(sample.get(filepath_key) or "").strip()
    return Path(fallback).expanduser().resolve() if fallback else Path()


def is_audio_sample(
    sample: Dict[str, Any],
    filepath_key: str = "filePath",
    filetype_key: str = "fileType",
    target_type_key: str = "target_type",
    data_key: str = "data",
) -> bool:
    if is_reference_sample(sample, filepath_key):
        return False
    data = sample.get(data_key)
    if isinstance(data, (bytes, bytearray)) and data:
        return True
    if _has_audio_path_hint(sample):
        return True
    if _has_audio_ext_params_hint(sample):
        return True
    return _ext_from_sample(sample, filepath_key, filetype_key, target_type_key) in AUDIO_EXTS


def invalid_quality_reason(sample: Dict[str, Any], ext_params_key: str = "ext_params") -> str:
    return ""


def mark_skipped_sample(
    sample: Dict[str, Any],
    reason: str,
    op_name: str,
    text_key: str = "text",
    data_key: str = "data",
    filetype_key: str = "fileType",
    target_type_key: str = "target_type",
    ext_params_key: str = "ext_params",
) -> Dict[str, Any]:
    ext = sample.get(ext_params_key, {})
    if not isinstance(ext, dict):
        ext = {"_raw": ext}
    ext.setdefault("audio_skip", {})[op_name] = reason
    sample[ext_params_key] = ext
    sample[text_key] = ""
    sample[data_key] = b""
    sample[filetype_key] = ""
    sample[target_type_key] = ""
    logger.info(f"fileName: {sample.get('fileName')}, method: {op_name} skipped: {reason}")
    return sample
