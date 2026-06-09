# -- encoding: utf-8 --

from __future__ import annotations

import fcntl
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample, resolve_audio_input_path
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample, resolve_audio_input_path


DEFAULT_LID_MODEL_SOURCE = "/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa"
DEFAULT_LID_MODEL_SAVEDIR = "/models/AudioOperations/lid/_speechbrain_cache"
DEFAULT_LANGUAGE_FILE_PATH = "/dataset/{dataset_id}/references/language.jsonl"
DEFAULT_OUTPUT_MODE = "integrated"
LANGUAGE_LOCK_DIR = Path("/tmp/datamate_audio_fast_lang_id_locks")
LID_MARKER_RE = re.compile(r"(?:^|__)lid_(zh|en)(?:__|$)")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _audio_preprocessor_root() -> Path:
    return _repo_root()


def _resolve_lid_model_source(value: str, package_root: Path) -> str:
    raw = str(value or "").strip() or DEFAULT_LID_MODEL_SOURCE
    p = Path(raw).expanduser()
    if p.exists():
        return str(p)
    fallback = package_root / "models" / "lid" / "speechbrain_lang-id-voxlingua107-ecapa"
    if fallback.exists():
        return str(fallback)
    return raw


def _audio_ext(sample: Dict[str, Any], default_ext: str = "wav") -> str:
    ext = str(sample.get("target_type") or sample.get("fileType") or default_ext).strip().lower().lstrip(".")
    return ext or default_ext


def _normalize_language(value: object) -> str:
    lang = str(value or "").strip().lower()
    if lang in {"zh", "cn", "cmn", "chinese", "中文", "汉语"}:
        return "zh"
    if lang in {"en", "eng", "english", "英文", "英语"}:
        return "en"
    return ""


def _normalize_lookup_key(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    stem = Path(raw).stem
    stem = LID_MARKER_RE.sub("", stem).rstrip("_")
    return stem.lower()


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


def _default_language_file_path(sample: Dict[str, Any]) -> Path:
    export_path = str(sample.get("export_path") or "")
    if export_path:
        return Path(export_path).expanduser() / "references" / "language.jsonl"

    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        return Path("/dataset") / dataset_id / "references" / "language.jsonl"

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / "references" / "language.jsonl"

    return Path("/dataset") / "references" / "language.jsonl"


def _resolve_language_file_path(path_value: str, sample: Dict[str, Any]) -> Path:
    raw_value = str(path_value or DEFAULT_LANGUAGE_FILE_PATH).strip()
    expanded = _expand_dataset_placeholders(raw_value, sample)
    if not expanded:
        return _default_language_file_path(sample)
    if raw_value == DEFAULT_LANGUAGE_FILE_PATH and sample.get("export_path"):
        return _default_language_file_path(sample)
    if _has_unresolved_dataset_placeholder(expanded):
        return _default_language_file_path(sample)

    p = Path(expanded).expanduser()
    if p.is_absolute():
        return p

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / p
    return (_repo_root() / p).resolve()


def _source_file_name(sample: Dict[str, Any], fallback_path: Path) -> str:
    for key in ("fileName", "sourceFileName", "filename"):
        value = str(sample.get(key) or "").strip()
        if value:
            return Path(value).name
    if str(fallback_path) not in {"", "."}:
        return fallback_path.name
    return "sample.wav"


def _language_record_keys(row: Dict[str, Any]) -> Set[str]:
    keys = set()
    for field in ("key", "file", "filename", "fileName", "wav", "audio", "path"):
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
    return row, _language_record_keys(row)


def _upsert_language_jsonl(path: Path, file_name: str, lang: str) -> None:
    lang = _normalize_language(lang) or "en"
    file_name = Path(file_name).name
    stem = Path(file_name).stem
    record = {
        "file": file_name,
        "fileName": file_name,
        "key": stem,
        "lang": lang,
    }
    record_keys = _language_record_keys(record)
    lock_name = hashlib.sha1(str(path).encode("utf-8")).hexdigest() + ".lock"
    LANGUAGE_LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = LANGUAGE_LOCK_DIR / lock_name

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


def _sample_lookup_keys(sample: Dict[str, Any]) -> Set[str]:
    keys = set()
    for field in ("fileName", "sourceFileName", "filename", "filePath"):
        key = _normalize_lookup_key(sample.get(field))
        if key:
            keys.add(key)
    return keys


def _already_processed(sample: Dict[str, Any], ext_params_key: str) -> bool:
    ext = sample.get(ext_params_key, {})
    if not isinstance(ext, dict):
        return False
    audio_lid = ext.get("audio_lid", {})
    if not isinstance(audio_lid, dict) or not audio_lid.get("audio_fast_lang_id_done"):
        return False

    processed_keys = set()
    for field in ("file", "fileName", "key"):
        key = _normalize_lookup_key(audio_lid.get(field))
        if key:
            processed_keys.add(key)
    return bool(processed_keys and processed_keys & _sample_lookup_keys(sample))


class AudioFastLangId(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_source = str(kwargs.get("modelSource", "")).strip()
        self.model_savedir = DEFAULT_LID_MODEL_SAVEDIR
        self.batch_size = 1
        self.max_seconds = float(kwargs.get("maxSeconds", 3.0))
        self.output_mode = str(kwargs.get("outputMode", DEFAULT_OUTPUT_MODE)).strip().lower() or DEFAULT_OUTPUT_MODE
        if self.output_mode in {"standalone", "single", "text", "label", "独立"}:
            self.output_mode = "standalone"
        else:
            self.output_mode = "integrated"
        self.language_file_path = str(kwargs.get("languageFilePath", DEFAULT_LANGUAGE_FILE_PATH)).strip()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        if _already_processed(sample, self.ext_params_key):
            return sample

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

        package_root = _audio_preprocessor_root()
        utils_dir = package_root / "helpers" / "utils"
        if str(utils_dir) not in sys.path:
            sys.path.insert(0, str(utils_dir))

        import fast_lang_id  # type: ignore

        with tempfile.TemporaryDirectory(prefix="dm_audio_lid_") as td:
            work_dir = Path(td)
            data = sample.get(self.data_key)
            audio_bytes_for_export = b""
            if isinstance(data, (bytes, bytearray)) and data:
                audio_bytes_for_export = bytes(data)
                wav_path = work_dir / f"input.{_audio_ext(sample)}"
                wav_path.write_bytes(audio_bytes_for_export)
                source_path = resolve_audio_input_path(sample, self.filepath_key)
            else:
                wav_path = resolve_audio_input_path(sample, self.filepath_key)
                if not wav_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {wav_path}")
                audio_bytes_for_export = wav_path.read_bytes()
                source_path = wav_path

            out_path = work_dir / "item_with_lang.list"
            in_list = work_dir / "single_item.list"
            file_name = _source_file_name(sample, source_path)
            in_list.write_text(
                json.dumps({"key": Path(file_name).stem, "wav": str(wav_path), "txt": ""}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            argv_backup = sys.argv[:]
            try:
                sys.argv = [
                    sys.argv[0],
                    "--input_list",
                    str(in_list),
                    "--output",
                    str(out_path),
                    "--device",
                    "cpu",
                    "--batch_size",
                    str(max(1, self.batch_size)),
                    "--max_seconds",
                    str(self.max_seconds),
                ]
                model_source = _resolve_lid_model_source(self.model_source, package_root)
                model_savedir = self.model_savedir or DEFAULT_LID_MODEL_SAVEDIR
                sys.argv += ["--model_source", model_source, "--model_savedir", model_savedir]

                rc = fast_lang_id.main()
                if rc != 0:
                    raise RuntimeError(f"fast_lang_id 失败，返回码: {rc}")
            finally:
                sys.argv = argv_backup

            if not out_path.exists():
                raise RuntimeError(f"LID 输出不存在: {out_path}")
            lines = [line.strip() for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if not lines:
                raise RuntimeError(f"LID 输出为空: {out_path}")
            d = json.loads(lines[0])
            lang = _normalize_language(d.get("lang")) or "en"

        language_file = ""
        if self.output_mode == "integrated":
            language_path = _resolve_language_file_path(self.language_file_path, sample)
            _upsert_language_jsonl(language_path, file_name, lang)
            language_file = str(language_path)

        ext_raw = sample.get(self.ext_params_key, {})
        if isinstance(ext_raw, dict):
            ext = dict(ext_raw)
        else:
            ext = {"_raw": ext_raw}
        ext["audio_lid"] = {
            "lang": lang,
            "mode": self.output_mode,
            "language_file": language_file,
            "audio_fast_lang_id_done": True,
            "file": file_name,
            "fileName": file_name,
            "key": Path(file_name).stem,
        }
        sample[self.ext_params_key] = ext

        if self.output_mode == "standalone":
            sample[self.data_key] = b""
            sample[self.text_key] = lang
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = "txt"
        else:
            target_ext = _audio_ext(sample)
            sample[self.data_key] = audio_bytes_for_export
            sample[self.text_key] = ""
            sample[self.target_type_key] = target_ext
            if self.is_last_op:
                sample[self.filetype_key] = "txt"
            else:
                sample[self.filetype_key] = target_ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioFastLangId "
            f"mode={self.output_mode}, lang={lang}, language_file={language_file}, "
            f"costs {time.time() - start:6f} s"
        )
        return sample
