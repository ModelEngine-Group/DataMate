# -- encoding: utf-8 --

from __future__ import annotations

import fcntl
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from loguru import logger

from datamate.core.base_op import Mapper


DEFAULT_VALIDATION_REPORT_PATH = "/dataset/{dataset_id}/references/emotion_validation.jsonl"
DEFAULT_SUMMARY_PATH = "/dataset/{dataset_id}/references/emotion_validation_summary.json"
VALIDATION_LOCK_DIR = Path("/tmp/datamate_audio_test_emotion_validation_locks")


RAVDESS_EMOTION_MAP = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry",
    "06": "fearful",
    "07": "disgust",
    "08": "surprised",
}


def _dataset_root_from_path(path_value: str) -> Path:
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


def _default_report_path(sample: Dict[str, Any], filename: str) -> Path:
    export_path = str(sample.get("export_path") or "").strip()
    if export_path:
        return Path(export_path).expanduser() / "references" / filename

    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        return Path("/dataset") / dataset_id / "references" / filename

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / "references" / filename

    return Path("/dataset") / "references" / filename


def _resolve_report_path(path_value: str, sample: Dict[str, Any], default_value: str, filename: str) -> Path:
    raw_value = str(path_value or default_value).strip()
    expanded = _expand_dataset_placeholders(raw_value, sample)
    if not expanded:
        return _default_report_path(sample, filename)
    if raw_value == default_value and sample.get("export_path"):
        return _default_report_path(sample, filename)
    if _has_unresolved_dataset_placeholder(expanded):
        return _default_report_path(sample, filename)

    p = Path(expanded).expanduser()
    if p.is_absolute():
        return p

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_path(file_path)
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
    return "sample.txt"


def _audio_name_from_output_name(file_name: str) -> str:
    path = Path(file_name)
    if path.suffix.lower() == ".txt":
        return path.with_suffix(".wav").name
    return path.name


def _normalize_emotion(value: object) -> str:
    text = str(value or "").strip().lower()
    aliases = {
        "fear": "fearful",
        "fearfulness": "fearful",
        "surprise": "surprised",
        "surprize": "surprised",
        "happiness": "happy",
        "anger": "angry",
        "sadness": "sad",
        "disgusted": "disgust",
    }
    return aliases.get(text, text)


def _expected_from_ravdess_name(file_name: str) -> Tuple[str, str]:
    stem = Path(file_name).stem
    parts = stem.split("-")
    if len(parts) < 3:
        return "", ""
    code = parts[2]
    return RAVDESS_EMOTION_MAP.get(code, ""), code


def _prediction_from_sample(sample: Dict[str, Any], text_key: str, filepath_key: str) -> str:
    text = str(sample.get(text_key) or "").strip()
    if text:
        first = text.splitlines()[0].strip()
        if first:
            return _normalize_emotion(first)

    data = sample.get("data")
    if isinstance(data, (bytes, bytearray)) and data:
        try:
            return _normalize_emotion(bytes(data).decode("utf-8-sig").strip().splitlines()[0])
        except Exception:
            pass

    path = Path(str(sample.get(filepath_key) or "")).expanduser()
    if path.exists() and path.is_file():
        try:
            return _normalize_emotion(path.read_text(encoding="utf-8-sig", errors="ignore").strip().splitlines()[0])
        except Exception:
            return ""
    return ""


def _record_keys(row: Dict[str, Any]) -> Set[str]:
    keys = set()
    for field in ("key", "file", "fileName", "audio_file", "audioFile"):
        raw = str(row.get(field) or "").strip()
        if raw:
            keys.add(Path(raw).stem.lower())
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
    return row, _record_keys(row)


def _upsert_validation_record(report_path: Path, record: Dict[str, Any], summary_path: Path) -> Dict[str, Any]:
    record_keys = _record_keys(record)
    lock_name = hashlib.sha1((str(report_path) + "|" + str(summary_path)).encode("utf-8")).hexdigest() + ".lock"
    VALIDATION_LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = VALIDATION_LOCK_DIR / lock_name

    with lock_path.open("w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            rows: List[Dict[str, Any]] = []
            kept_lines: List[str] = []
            if report_path.exists():
                for line in report_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    row, keys = _parse_jsonl_record(line)
                    if row and keys & record_keys:
                        continue
                    if row:
                        rows.append(row)
                    if line.strip() and not (row and keys & record_keys):
                        kept_lines.append(line)

            rows.append(record)
            kept_lines.append(json.dumps(record, ensure_ascii=False))
            tmp_path = report_path.with_suffix(report_path.suffix + ".tmp")
            tmp_path.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
            tmp_path.replace(report_path)

            evaluated = sum(1 for row in rows if row.get("evaluated"))
            correct = sum(1 for row in rows if row.get("evaluated") and row.get("correct"))
            invalid = len(rows) - evaluated
            by_expected = Counter(str(row.get("expected") or "") for row in rows if row.get("evaluated"))
            by_predicted = Counter(str(row.get("predicted") or "") for row in rows if row.get("evaluated"))
            summary = {
                "total": len(rows),
                "evaluated": evaluated,
                "correct": correct,
                "incorrect": max(0, evaluated - correct),
                "invalid": invalid,
                "accuracy": round(correct / evaluated, 6) if evaluated else 0.0,
                "report": str(report_path),
                "by_expected": dict(sorted(by_expected.items())),
                "by_predicted": dict(sorted(by_predicted.items())),
            }
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_tmp = summary_path.with_suffix(summary_path.suffix + ".tmp")
            summary_tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary_tmp.replace(summary_path)
            return summary
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


class AudioTestEmotionResultValidation(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validation_report_path = str(kwargs.get("validationReportPath", DEFAULT_VALIDATION_REPORT_PATH)).strip()
        self.summary_path = str(kwargs.get("summaryPath", DEFAULT_SUMMARY_PATH)).strip()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        file_name = _source_file_name(sample, self.filename_key, self.filepath_key)
        audio_file = _audio_name_from_output_name(file_name)
        predicted = _prediction_from_sample(sample, self.text_key, self.filepath_key)
        expected, emotion_code = _expected_from_ravdess_name(audio_file)
        evaluated = bool(expected and predicted)
        correct = bool(evaluated and expected == predicted)
        record = {
            "file": file_name,
            "fileName": file_name,
            "audio_file": audio_file,
            "key": Path(audio_file).stem,
            "expected": expected,
            "predicted": predicted,
            "emotion_code": emotion_code,
            "correct": correct,
            "evaluated": evaluated,
        }

        report_path = _resolve_report_path(
            self.validation_report_path,
            sample,
            DEFAULT_VALIDATION_REPORT_PATH,
            "emotion_validation.jsonl",
        )
        summary_path = _resolve_report_path(
            self.summary_path,
            sample,
            DEFAULT_SUMMARY_PATH,
            "emotion_validation_summary.json",
        )
        summary = _upsert_validation_record(report_path, record, summary_path)
        record["validation_report"] = str(report_path)
        record["summary_report"] = str(summary_path)
        record["accuracy_so_far"] = summary.get("accuracy", 0.0)

        ext_raw = sample.get(self.ext_params_key, {})
        if isinstance(ext_raw, dict):
            ext = dict(ext_raw)
        else:
            ext = {"_raw": ext_raw}
        ext["audio_test_emotion_result_validation"] = record
        sample[self.ext_params_key] = ext
        sample[self.text_key] = json.dumps(record, ensure_ascii=False)
        sample[self.data_key] = b""
        sample[self.filetype_key] = "txt"
        sample[self.target_type_key] = "txt"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioTestEmotionResultValidation "
            f"expected={expected}, predicted={predicted}, correct={correct}, "
            f"accuracy={summary.get('accuracy', 0.0)}, costs {time.time() - start:6f} s"
        )
        return sample
