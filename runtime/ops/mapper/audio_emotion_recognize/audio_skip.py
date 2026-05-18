# -- encoding: utf-8 --

from pathlib import Path
from typing import Any, Dict

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)


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
    return _ext_from_sample(sample, filepath_key, filetype_key, target_type_key) in AUDIO_EXTS


def invalid_quality_reason(sample: Dict[str, Any], ext_params_key: str = "ext_params") -> str:
    for key in ("fileName", "sourceFileName", "filePath"):
        marker_source = Path(str(sample.get(key) or "")).stem.lower()
        marker = "__quality_invalid"
        if marker in marker_source:
            reason = marker_source.split(marker, 1)[1].strip("_") or "invalid_audio"
            return f"invalid_audio_quality:{reason}"

    ext = sample.get(ext_params_key, {})
    if not isinstance(ext, dict):
        return ""
    quality = ext.get("audio_quality", {})
    if not isinstance(quality, dict):
        return ""
    if str(quality.get("quality_flag") or "").strip().lower() != "invalid":
        return ""
    skip_downstream = quality.get("skip_downstream", True)
    if isinstance(skip_downstream, str):
        skip_downstream = skip_downstream.strip().lower() in {"1", "true", "yes", "y", "on"}
    if not skip_downstream:
        return ""
    reason = str(quality.get("reason") or "invalid_audio").strip()
    return f"invalid_audio_quality:{reason}"


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
