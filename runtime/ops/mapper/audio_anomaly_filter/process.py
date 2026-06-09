# -- encoding: utf-8 --

import fcntl
import hashlib
import json
import math
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from loguru import logger

from datamate.core.base_op import Mapper

try:
    from .audio_skip import is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import is_audio_sample, mark_skipped_sample


DEFAULT_ANOMALY_REPORT_PATH = "/dataset/{dataset_id}/references/anomaly_report.jsonl"
ANOMALY_LOCK_DIR = Path("/tmp/datamate_audio_anomaly_filter_locks")


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on", "保留", "开启"}


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


def _dataset_root_from_audio_path(path_value: str) -> Path:
    if not path_value:
        return Path()
    p = Path(path_value).expanduser()
    parts = p.parts
    for idx, part in enumerate(parts):
        if part == "dataset" and idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return p.parent


def _expand_dataset_placeholders(path_value: str, sample: Dict[str, Any]) -> str:
    value = str(path_value or "").strip()
    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        value = value.replace("{dataset_id}", dataset_id).replace("${dataset_id}", dataset_id)
        value = value.replace("{datasetId}", dataset_id).replace("${datasetId}", dataset_id)
    return value


def _has_unresolved_dataset_placeholder(path_value: str) -> bool:
    return any(token in path_value for token in ("{dataset_id}", "${dataset_id}", "{datasetId}", "${datasetId}"))


def _default_anomaly_report_path(sample: Dict[str, Any]) -> Path:
    export_path = str(sample.get("export_path") or "").strip()
    if export_path:
        return Path(export_path).expanduser() / "references" / "anomaly_report.jsonl"

    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        return Path("/dataset") / dataset_id / "references" / "anomaly_report.jsonl"

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / "references" / "anomaly_report.jsonl"

    return Path("/dataset") / "references" / "anomaly_report.jsonl"


def _resolve_anomaly_report_path(path_value: str, sample: Dict[str, Any]) -> Path:
    raw_value = str(path_value or DEFAULT_ANOMALY_REPORT_PATH).strip()
    expanded = _expand_dataset_placeholders(raw_value, sample)
    if not expanded:
        return _default_anomaly_report_path(sample)
    if raw_value == DEFAULT_ANOMALY_REPORT_PATH and sample.get("export_path"):
        return _default_anomaly_report_path(sample)
    if _has_unresolved_dataset_placeholder(expanded):
        return _default_anomaly_report_path(sample)

    p = Path(expanded).expanduser()
    if p.is_absolute():
        return p

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / p
    return (Path(__file__).resolve().parent / p).resolve()


def _source_file_name(sample: Dict[str, Any], filename_key: str, filepath_key: str) -> str:
    for key in (filename_key, "sourceFileName", "filename"):
        value = str(sample.get(key) or "").strip()
        if value:
            return Path(value).name
    path_value = str(sample.get(filepath_key) or "").strip()
    if path_value:
        return Path(path_value).name
    return "sample.wav"


def _normalize_lookup_key(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    return Path(raw).stem.lower()


def _anomaly_record_keys(row: Dict[str, Any]) -> Set[str]:
    keys = set()
    for field in ("key", "file", "fileName", "filename", "path"):
        key = _normalize_lookup_key(row.get(field))
        if key:
            keys.add(key)
    return keys


def _parse_jsonl_record(line: str) -> Tuple[Dict[str, Any], Set[str]]:
    text = line.strip()
    if not text or not text.startswith("{"):
        return {}, set()
    try:
        row = json.loads(text)
    except Exception:
        return {}, set()
    if not isinstance(row, dict):
        return {}, set()
    return row, _anomaly_record_keys(row)


def _upsert_anomaly_report(path: Path, file_name: str, report: Dict[str, Any], keep_invalid_audio: bool) -> None:
    file_name = Path(file_name).name
    record = {
        "file": file_name,
        "fileName": file_name,
        "key": Path(file_name).stem,
        "reason": report.get("reason", ""),
        "read_error": report.get("read_error", ""),
        "duration": report.get("duration", 0.0),
        "silence_ratio": report.get("silence_ratio", 0.0),
        "global_rms": report.get("global_rms", 0.0),
        "keep_invalid_audio": keep_invalid_audio,
    }
    record_keys = _anomaly_record_keys(record)
    lock_name = hashlib.sha1(str(path).encode("utf-8")).hexdigest() + ".lock"
    ANOMALY_LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = ANOMALY_LOCK_DIR / lock_name

    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            kept_lines: List[str] = []
            if path.exists():
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    row, keys = _parse_jsonl_record(line)
                    if row and keys & record_keys:
                        continue
                    if line.strip():
                        kept_lines.append(line)
            kept_lines.append(json.dumps(record, ensure_ascii=False))
            tmp_path = path.with_suffix(path.suffix + ".tmp")
            tmp_path.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
            tmp_path.replace(path)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


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
        self.keep_invalid_audio = _as_bool(kwargs.get("keepInvalidAudio", False))
        self.anomaly_report_path = str(kwargs.get("anomalyReportPath", DEFAULT_ANOMALY_REPORT_PATH)).strip()

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
            "keep_invalid_audio": self.keep_invalid_audio,
        }
        ext_raw = sample.get(self.ext_params_key, {})
        if isinstance(ext_raw, dict):
            ext = dict(ext_raw)
        else:
            ext = {"_raw": ext_raw}
        ext["audio_quality"] = report
        sample[self.ext_params_key] = ext

        source_file_name = _source_file_name(sample, self.filename_key, self.filepath_key)
        anomaly_report_file = ""
        if quality_flag == "invalid":
            report_path = _resolve_anomaly_report_path(self.anomaly_report_path, sample)
            _upsert_anomaly_report(report_path, source_file_name, report, self.keep_invalid_audio)
            anomaly_report_file = str(report_path)
            ext["audio_quality"]["anomaly_report_file"] = anomaly_report_file
            sample[self.ext_params_key] = ext
            if not self.keep_invalid_audio:
                sample[self.text_key] = ""
                sample[self.data_key] = b""
                sample[self.filetype_key] = ""
                sample[self.target_type_key] = ""
                sample[self.filepath_key] = ""
                logger.info(
                    f"fileName: {sample.get(self.filename_key)}, method: AudioAnomalyFilter "
                    f"filtered invalid audio, report={anomaly_report_file}, costs {time.time() - start:6f} s"
                )
                return sample

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

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAnomalyFilter "
            f"quality={quality_flag}, report={anomaly_report_file}, costs {time.time() - start:6f} s"
        )
        return sample
