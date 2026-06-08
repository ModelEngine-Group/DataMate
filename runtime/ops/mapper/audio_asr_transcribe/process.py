# -- encoding: utf-8 --

from __future__ import annotations

import contextlib
import fcntl
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


DEFAULT_ZH_MODEL_DIR = "/models/AudioOperations/asr/aishell"
DEFAULT_EN_MODEL_DIR = "/models/AudioOperations/asr/librispeech"
DEFAULT_LANGUAGE_FILE_PATH = "/dataset/{dataset_id}/references/language.jsonl"
DEFAULT_MAX_CONCURRENT_FILES = 1
FIXED_DECODE_MODE = "ctc_greedy_search"
LID_MARKER_RE = re.compile(r"(?:^|__)lid_(zh|en)(?:__|$)")
LANGUAGE_FILE_NAMES = ("language.jsonl", "language.txt", "language.tsv")
ASR_LOCK_PATH = "/tmp/datamate_audio_asr_transcribe.lock"


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _helper_root() -> Path:
    return _package_root() / "audio_preprocessor"


@contextlib.contextmanager
def _asr_runtime_lock(max_concurrent_files: int):
    if max_concurrent_files > 1:
        yield
        return

    Path(ASR_LOCK_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(ASR_LOCK_PATH, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _model_dir(language: str, zh_model_dir: str, en_model_dir: str) -> Path:
    if language == "zh":
        return Path(zh_model_dir or DEFAULT_ZH_MODEL_DIR).expanduser().resolve()
    if language == "en":
        return Path(en_model_dir or DEFAULT_EN_MODEL_DIR).expanduser().resolve()
    raise ValueError(f"不支持的语言: {language}")


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


def _expand_dataset_placeholders(path_value: str, sample: Dict[str, Any]) -> str:
    value = str(path_value or "").strip()
    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        value = value.replace("{dataset_id}", dataset_id).replace("${dataset_id}", dataset_id)
        value = value.replace("{datasetId}", dataset_id).replace("${datasetId}", dataset_id)
    return value


def _resolve_optional_path(path_value: str, sample: Dict[str, Any]) -> Path:
    value = _expand_dataset_placeholders(path_value, sample)
    if "{dataset_id}" in value or "${dataset_id}" in value or "{datasetId}" in value or "${datasetId}" in value:
        return Path()
    if not value:
        return Path()
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = (_package_root() / p).resolve()
    return p


def _append_language_candidates_from_root(candidates: List[Path], root: Path) -> None:
    candidates.append(root / "references" / "language.jsonl")
    candidates.append(root / "references" / "language.txt")
    candidates.append(root / "references" / "language.tsv")
    candidates.append(root / "reference" / "language.jsonl")
    candidates.append(root / "reference" / "language.txt")
    candidates.append(root / "reference" / "language.tsv")
    candidates.append(root / "language.jsonl")
    candidates.append(root / "language.txt")


def _append_recursive_language_candidates(candidates: List[Path], root: Path) -> None:
    if not root.exists() or not root.is_dir():
        return
    for name in LANGUAGE_FILE_NAMES:
        try:
            candidates.extend(sorted(p for p in root.rglob(name) if p.is_file()))
        except Exception:
            continue


def _iter_flow_dataset_jsonl(sample: Dict[str, Any]) -> Iterable[Path]:
    task_ids = []
    for key in ("instance_id", "instanceId", "task_id", "taskId"):
        value = str(sample.get(key) or "").strip()
        if value and value not in task_ids:
            task_ids.append(value)

    for task_id in task_ids:
        for name in ("dataset.jsonl", "dataset_on_dj.jsonl"):
            path = Path("/flow") / task_id / name
            if path.exists() and path.is_file():
                yield path


def _append_language_candidates_from_flow(candidates: List[Path], sample: Dict[str, Any]) -> None:
    for dataset_jsonl in _iter_flow_dataset_jsonl(sample):
        try:
            rows = dataset_jsonl.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as exc:
            logger.warning(f"AudioAsrTranscribe failed to read flow dataset index: {dataset_jsonl}, error={exc}")
            continue

        source_roots: List[Path] = []
        for line in rows:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict):
                continue

            file_name = str(row.get("fileName") or row.get("filename") or "").strip()
            file_path = str(row.get("filePath") or row.get("path") or "").strip()
            if not file_path:
                continue
            path = Path(file_path).expanduser()
            if path.name in LANGUAGE_FILE_NAMES or file_name in LANGUAGE_FILE_NAMES:
                candidates.append(path)

            root = _dataset_root_from_audio_path(file_path)
            if str(root) not in {"", "."} and root not in source_roots:
                source_roots.append(root)

        for root in source_roots:
            _append_language_candidates_from_root(candidates, root)


def _dataset_root_from_audio_path(path_value: str) -> Path:
    if not path_value:
        return Path()
    p = Path(path_value).expanduser()
    parts = p.parts
    for idx, part in enumerate(parts):
        if part == "dataset" and idx + 1 < len(parts):
            return Path(*parts[: idx + 2])
    return p.parent


def _language_file_candidates(language_file_path: str, sample: Dict[str, Any]) -> List[Path]:
    candidates: List[Path] = []
    configured = _resolve_optional_path(language_file_path or DEFAULT_LANGUAGE_FILE_PATH, sample)
    if str(configured) not in {"", "."}:
        candidates.append(configured)

    recursive_roots: List[Path] = []

    _append_language_candidates_from_flow(candidates, sample)

    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        dataset_root = Path("/dataset") / dataset_id
        _append_language_candidates_from_root(candidates, dataset_root)
        recursive_roots.append(dataset_root)
        # Some deployments mount dataset files under /datasets.
        datasets_root = Path("/datasets") / dataset_id
        _append_language_candidates_from_root(candidates, datasets_root)
        recursive_roots.append(datasets_root)

    sample_file_value = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(sample_file_value)
    if str(dataset_root) not in {"", "."}:
        _append_language_candidates_from_root(candidates, dataset_root)
        recursive_roots.append(dataset_root)

    export_root = Path(str(sample.get("export_path") or "")).expanduser()
    if str(export_root) not in {"", "."}:
        _append_language_candidates_from_root(candidates, export_root)
        recursive_roots.append(export_root)

    sample_file = Path(sample_file_value).expanduser()
    if str(sample_file) not in {"", "."}:
        for parent in [sample_file.parent, *sample_file.parents]:
            _append_language_candidates_from_root(candidates, parent)

    for root in recursive_roots:
        _append_recursive_language_candidates(candidates, root)

    # Last-resort sidecar scan. DataMate treats reference files as independent
    # samples and filters them from the audio flow, so the audio sample may not
    # carry a direct pointer to language.jsonl. The file still exists on disk
    # under /dataset in normal deployments.
    for root in (Path("/dataset"), Path("/datasets")):
        _append_recursive_language_candidates(candidates, root)

    seen = set()
    unique: List[Path] = []
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except Exception:
            resolved = candidate
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _parse_language_mapping_line(line: str) -> Tuple[str, str]:
    text = line.strip()
    if not text or text.startswith("#"):
        return "", ""

    if text.startswith("{") and text.endswith("}"):
        try:
            row = json.loads(text)
        except Exception:
            row = {}
        if isinstance(row, dict):
            key = (
                row.get("key")
                or row.get("file")
                or row.get("filename")
                or row.get("fileName")
                or row.get("wav")
                or row.get("audio")
                or row.get("path")
            )
            lang = _normalize_language(row.get("lang") or row.get("language"))
            return _normalize_lookup_key(key), lang

    parts = re.split(r"[\t, ]+", text, maxsplit=1)
    if len(parts) < 2:
        return "", ""

    first, second = parts[0].strip(), parts[1].strip()
    first_lang = _normalize_language(first)
    second_lang = _normalize_language(second)
    if second_lang:
        return _normalize_lookup_key(first), second_lang
    if first_lang:
        return _normalize_lookup_key(second), first_lang
    return "", ""


def _load_language_mapping(path: Path) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        key, lang = _parse_language_mapping_line(line)
        if key and lang:
            mapping[key] = lang
    return mapping


def _read_language_from_mapping(
    language_file_path: str,
    sample: Dict[str, Any],
    lookup_keys: List[str],
    cache: Dict[str, Dict[str, str]],
) -> Tuple[str, str, str]:
    lookup = {_normalize_lookup_key(k) for k in lookup_keys if _normalize_lookup_key(k)}
    if not lookup:
        return "", "", ""

    existing_candidates: List[str] = []
    for candidate in _language_file_candidates(language_file_path, sample):
        if not candidate.exists() or not candidate.is_file():
            continue
        candidate_s = str(candidate)
        existing_candidates.append(candidate_s)
        if candidate_s not in cache:
            cache[candidate_s] = _load_language_mapping(candidate)
            logger.info(
                f"AudioAsrTranscribe loaded language file: file={candidate}, rows={len(cache[candidate_s])}"
            )
        mapping = cache[candidate_s]
        for key in lookup:
            lang = mapping.get(key, "")
            if key and lang and key in lookup:
                logger.info(
                    f"AudioAsrTranscribe language lookup matched: lang={lang}, key={key}, file={candidate}"
                )
                return lang, str(candidate), key
    candidate_preview = []
    for candidate in _language_file_candidates(language_file_path, sample):
        candidate_s = str(candidate)
        if candidate_s not in candidate_preview:
            candidate_preview.append(candidate_s)
        if len(candidate_preview) >= 12:
            break
    logger.warning(
        "AudioAsrTranscribe language lookup not matched; "
        f"lookup_keys={sorted(lookup)}, existing_language_files={existing_candidates[:10]}, "
        f"candidate_preview={candidate_preview}"
    )
    return "", "", ""


def _resolve_language(
    language: str,
    sample: Dict[str, Any],
    language_file_path: str,
    lookup_keys: List[str],
    language_cache: Dict[str, Dict[str, str]],
) -> Tuple[str, str, str, str]:
    requested_language = _normalize_language(language) or str(language or "").strip().lower()

    lang, source, matched_key = _read_language_from_mapping(language_file_path, sample, lookup_keys, language_cache)
    if lang:
        return lang, "language_file", source, matched_key

    if requested_language in {"zh", "en"}:
        return requested_language, "param", "", ""
    if requested_language != "auto":
        raise ValueError(f"不支持的语言: {language}")

    return "zh", "default_zh", "", ""


def _audio_ext(sample: Dict[str, Any], default_ext: str = "wav") -> str:
    ext = str(sample.get("target_type") or sample.get("fileType") or default_ext).strip().lower().lstrip(".")
    return ext or default_ext


def _read_text_result(path: Path) -> str:
    if not path.exists():
        return ""
    results = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            results.append(parts[1].strip())
    return "\n".join(results)


def _read_raw_result(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def _sample_key(sample: Dict[str, Any], fallback_path: Path, filename_key: str) -> str:
    file_name = str(sample.get(filename_key) or "").strip()
    if file_name:
        return LID_MARKER_RE.sub("", Path(file_name).stem).rstrip("_") or Path(file_name).stem
    return fallback_path.stem


def _prepare_asr_segments(audio_path: Path, work_dir: Path, key: str, max_seconds: int) -> List[Tuple[str, Path]]:
    """Normalize ASR input to 16kHz mono wav and split long audio into segments."""
    try:
        import torchaudio

        waveform, sample_rate = torchaudio.load(str(audio_path))
        if waveform.numel() == 0:
            return [(key, audio_path)]
        if waveform.dim() == 1:
            waveform = waveform.unsqueeze(0)
        if waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if int(sample_rate) != 16000:
            waveform = torchaudio.functional.resample(waveform, int(sample_rate), 16000)
            sample_rate = 16000

        segment_samples = max(1, int(max_seconds)) * int(sample_rate)
        total_samples = int(waveform.size(1))
        if total_samples <= segment_samples:
            normalized_path = work_dir / f"{key}.wav"
            torchaudio.save(str(normalized_path), waveform.cpu(), int(sample_rate))
            return [(key, normalized_path)]

        segments: List[Tuple[str, Path]] = []
        start = 0
        index = 0
        while start < total_samples:
            end = min(start + segment_samples, total_samples)
            segment = waveform[:, start:end]
            segment_key = f"{key}_part{index}"
            segment_path = work_dir / f"{segment_key}.wav"
            torchaudio.save(str(segment_path), segment.cpu(), int(sample_rate))
            segments.append((segment_key, segment_path))
            start = end
            index += 1
        return segments
    except Exception as e:
        logger.warning(f"ASR 音频标准化/切分失败，继续使用原始音频: {e}")
        return [(key, audio_path)]


def _prepare_wenet_cwd(work_dir: Path, model_dir: Path, language: str) -> Path:
    asr_dir_name = "aishell" if language == "zh" else "librispeech"
    link_dir = work_dir / "models" / "asr" / asr_dir_name
    link_dir.parent.mkdir(parents=True, exist_ok=True)
    if not link_dir.exists():
        link_dir.symlink_to(model_dir, target_is_directory=True)
    return work_dir


class AudioAsrTranscribe(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language = str(kwargs.get("language", "auto")).strip().lower()
        self.language_file_path = str(kwargs.get("languageFilePath", DEFAULT_LANGUAGE_FILE_PATH)).strip()
        self.zh_model_dir = str(kwargs.get("zhModelDir", DEFAULT_ZH_MODEL_DIR)).strip()
        self.en_model_dir = str(kwargs.get("enModelDir", DEFAULT_EN_MODEL_DIR)).strip()
        self.mode = FIXED_DECODE_MODE
        self.batch_size = int(float(kwargs.get("batchSize", 1)))
        self.max_segment_seconds = int(float(kwargs.get("maxSegmentSeconds", 120)))
        self.max_concurrent_files = max(1, int(float(kwargs.get("maxConcurrentFiles", DEFAULT_MAX_CONCURRENT_FILES))))
        self.language_cache: Dict[str, Dict[str, str]] = {}

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

        helper_root = _helper_root()
        run_wenet = helper_root / "src" / "utils" / "run_wenet.py"
        if not run_wenet.exists():
            raise FileNotFoundError(f"WeNet 包装器不存在: {run_wenet}")

        with tempfile.TemporaryDirectory(prefix="dm_audio_asr_transcribe_") as td:
            work_dir = Path(td)
            data = sample.get(self.data_key)
            if isinstance(data, (bytes, bytearray)) and data:
                audio_path = work_dir / f"input.{_audio_ext(sample)}"
                audio_path.write_bytes(bytes(data))
            else:
                audio_path = Path(str(sample.get(self.filepath_key, ""))).expanduser().resolve()
                if not audio_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {audio_path}")

            key = _sample_key(sample, audio_path, self.filename_key)
            lookup_keys = [
                key,
                Path(str(sample.get(self.filename_key) or "")).name,
                Path(str(sample.get("sourceFileName") or "")).name,
                audio_path.name,
                audio_path.stem,
            ]
            actual_language, language_source, language_file_used, language_matched_key = _resolve_language(
                self.language,
                sample,
                self.language_file_path,
                lookup_keys,
                self.language_cache,
            )
            logger.info(
                "AudioAsrTranscribe resolved language: "
                f"fileName={sample.get(self.filename_key)}, requested={self.language}, "
                f"resolved={actual_language}, source={language_source}, "
                f"language_file={language_file_used}, matched_key={language_matched_key}, "
                f"lookup_keys={lookup_keys}"
            )
            model_dir = _model_dir(actual_language, self.zh_model_dir, self.en_model_dir)
            config_path = model_dir / "train.yaml"
            checkpoint_path = model_dir / "final.pt"
            units_path = model_dir / "units.txt"
            if not config_path.exists():
                raise FileNotFoundError(f"ASR 配置不存在: {config_path}")
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"ASR 模型不存在: {checkpoint_path}")
            if not units_path.exists():
                raise FileNotFoundError(f"ASR units 文件不存在: {units_path}")

            with _asr_runtime_lock(self.max_concurrent_files):
                asr_segments = _prepare_asr_segments(
                    audio_path,
                    work_dir,
                    key,
                    max_seconds=max(1, self.max_segment_seconds),
                )
                list_path = work_dir / "single_audio.list"
                result_dir = work_dir / "result"
                wenet_cwd = _prepare_wenet_cwd(work_dir, model_dir, actual_language)
                result_dir.mkdir(parents=True, exist_ok=True)
                with list_path.open("w", encoding="utf-8") as f:
                    for segment_key, segment_path in asr_segments:
                        f.write(
                            json.dumps({"key": segment_key, "wav": str(segment_path), "txt": ""}, ensure_ascii=False)
                            + "\n"
                        )

                cmd = [
                    sys.executable,
                    str(run_wenet),
                    "--modes",
                    self.mode,
                    "--device",
                    "cpu",
                    "--config",
                    str(config_path),
                    "--test_data",
                    str(list_path),
                    "--checkpoint",
                    str(checkpoint_path),
                    "--batch_size",
                    str(max(1, self.batch_size)),
                    "--result_dir",
                    str(result_dir),
                ]
                proc = subprocess.run(
                    cmd,
                    cwd=str(wenet_cwd),
                    env=dict(**os.environ),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            if proc.returncode != 0:
                raise RuntimeError(
                    "ASR 识别失败，返回码: "
                    f"{proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
                )

            transcript = ""
            selected_mode = self.mode
            raw_results: Dict[str, str] = {}
            text_results: Dict[str, str] = {}
            for mode in [self.mode]:
                text_path = result_dir / mode / "text"
                raw_results[mode] = _read_raw_result(text_path)
                text_results[mode] = _read_text_result(text_path)
                if text_results[mode] and not transcript:
                    transcript = text_results[mode]
                    selected_mode = mode

            transcript_source = "asr"

            if not transcript:
                raise RuntimeError(
                    "ASR 未识别出非空文本。"
                    f"language={actual_language}, mode={self.mode}, segments={len(asr_segments)}, "
                    f"raw_results={raw_results}, languageFilePath={self.language_file_path}"
                )

            ext = sample.get(self.ext_params_key, {})
            if not isinstance(ext, dict):
                ext = {"_raw": ext}
            ext["audio_asr_transcribe"] = {
                "language": actual_language,
                "language_param": self.language,
                "language_source": language_source,
                "language_file_path": language_file_used,
                "language_matched_key": language_matched_key,
                "mode": selected_mode,
                "requested_mode": self.mode,
                "modes_tried": [self.mode],
                "model_dir": str(model_dir),
                "segments": len(asr_segments),
                "max_segment_seconds": self.max_segment_seconds,
                "max_concurrent_files": self.max_concurrent_files,
                "transcript_source": transcript_source,
                "mode_text_empty": {self.mode: not bool(text_results.get(self.mode))},
                "transcript_empty": not bool(transcript),
            }
            sample[self.ext_params_key] = ext
            sample[self.text_key] = transcript
            sample[self.data_key] = b""
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = "txt"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioAsrTranscribe costs {time.time() - start:6f} s"
        )
        return sample
