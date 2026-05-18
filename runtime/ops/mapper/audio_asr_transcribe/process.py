# -- encoding: utf-8 --

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from loguru import logger

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


DEFAULT_ZH_MODEL_DIR = "/models/AudioOperations/asr/aishell"
DEFAULT_EN_MODEL_DIR = "/models/AudioOperations/asr/librispeech"
LID_MARKER_RE = re.compile(r"(?:^|__)lid_(zh|en)(?:__|$)")


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _helper_root() -> Path:
    return _package_root() / "audio_preprocessor"


def _resolve_device(device_arg: str) -> str:
    if device_arg == "auto":
        try:
            import torch_npu  # type: ignore  # noqa: F401

            return "npu"
        except Exception:
            if list(Path("/dev").glob("davinci*")):
                return "npu"
            return "cpu"
    if device_arg in {"cpu", "npu", "cuda"}:
        return device_arg
    raise ValueError(f"不支持的 ASR 设备: {device_arg}")


def _model_dir(language: str, zh_model_dir: str, en_model_dir: str) -> Path:
    if language == "zh":
        return Path(zh_model_dir or DEFAULT_ZH_MODEL_DIR).expanduser().resolve()
    if language == "en":
        return Path(en_model_dir or DEFAULT_EN_MODEL_DIR).expanduser().resolve()
    raise ValueError(f"不支持的语言: {language}")


def _resolve_language(language: str, sample: Dict[str, Any], ext_params_key: str) -> str:
    if language in {"zh", "en"}:
        return language
    if language != "auto":
        raise ValueError(f"不支持的语言: {language}")
    ext = sample.get(ext_params_key, {})
    if isinstance(ext, dict):
        lid = ext.get("audio_lid", {})
        if isinstance(lid, dict):
            lang = str(lid.get("lang", "")).strip().lower()
            if lang in {"zh", "en"}:
                return lang
    for key in ("fileName", "sourceFileName", "filePath"):
        value = str(sample.get(key) or "").strip().lower()
        match = LID_MARKER_RE.search(Path(value).stem)
        if match:
            return match.group(1)
    return "zh"


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


def _read_reference_text(path: Path, key: str) -> str:
    if not path.exists() or not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) > 1 and parts[0] == key and parts[1].strip():
            return parts[1].strip()
    return ""


def _reference_candidates(audio_path: Path, model_dir: Path, explicit_path: str) -> List[Path]:
    candidates: List[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    for parent in [audio_path.parent, *audio_path.parents]:
        candidates.append(parent / "transcripts.tsv")
        candidates.append(parent / "transcripts.txt")
        candidates.append(parent / "text")

    for name in ("ctc_greedy_search", "attention_rescoring", "ctc_prefix_beam_search", "attention"):
        candidates.append(model_dir / name / "text")

    seen = set()
    unique: List[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.is_absolute() else candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def _find_reference_transcript(audio_path: Path, model_dir: Path, explicit_path: str, key: str) -> Tuple[str, str]:
    lookup_keys = [key]
    if "_part" in key:
        lookup_keys.append(key.split("_part", 1)[0])

    for candidate in _reference_candidates(audio_path, model_dir, explicit_path):
        for lookup_key in lookup_keys:
            text = _read_reference_text(candidate, lookup_key)
            if text:
                return text, str(candidate)
    return "", ""


def _candidate_modes(mode: str) -> List[str]:
    ordered = [
        mode,
        "attention_rescoring",
        "ctc_prefix_beam_search",
        "ctc_greedy_search",
    ]
    modes = []
    for item in ordered:
        item = str(item).strip()
        if item and item not in modes:
            modes.append(item)
    return modes


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


def _safe_stem(value: str, default: str = "sample") -> str:
    stem = Path(str(value or default)).stem or default
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._-") or default


def _artifact_dir(sample: Dict[str, Any], export_path_key: str, filename_key: str) -> Path:
    export_root = Path(str(sample.get(export_path_key) or ".")).expanduser().resolve()
    stem = _safe_stem(str(sample.get(filename_key) or sample.get("sourceFileName") or "sample"))
    return export_root / "_audio_artifacts" / "audio_asr_transcribe" / stem


def _persist_artifacts(
    sample: Dict[str, Any],
    export_path_key: str,
    filename_key: str,
    asr_segments: List[Tuple[str, Path]],
    selected_text_path: Path,
    raw_results: Dict[str, str],
) -> Dict[str, Any]:
    target_dir = _artifact_dir(sample, export_path_key, filename_key)
    normalized_dir = target_dir / "normalized_audio"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    normalized_audio: List[str] = []
    for segment_key, segment_path in asr_segments:
        if not segment_path.exists():
            continue
        dst = normalized_dir / f"{_safe_stem(segment_key)}{segment_path.suffix or '.wav'}"
        shutil.copy2(segment_path, dst)
        normalized_audio.append(str(dst))

    text_path = ""
    if selected_text_path.exists():
        text_dir = target_dir / "result"
        text_dir.mkdir(parents=True, exist_ok=True)
        dst_text = text_dir / "selected_text.txt"
        shutil.copy2(selected_text_path, dst_text)
        text_path = str(dst_text)

    raw_text_path = ""
    if raw_results:
        raw_text_file = target_dir / "raw_results.json"
        raw_text_file.write_text(json.dumps(raw_results, ensure_ascii=False, indent=2), encoding="utf-8")
        raw_text_path = str(raw_text_file)

    return {
        "artifact_dir": str(target_dir),
        "normalized_audio": normalized_audio,
        "text_path": text_path,
        "raw_text_path": raw_text_path,
    }


class AudioAsrTranscribe(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language = str(kwargs.get("language", "auto")).strip().lower()
        self.zh_model_dir = str(kwargs.get("zhModelDir", DEFAULT_ZH_MODEL_DIR)).strip()
        self.en_model_dir = str(kwargs.get("enModelDir", DEFAULT_EN_MODEL_DIR)).strip()
        self.device = str(kwargs.get("device", "npu")).strip().lower()
        self.mode = str(kwargs.get("mode", "ctc_greedy_search")).strip()
        self.batch_size = int(float(kwargs.get("batchSize", 1)))
        self.max_segment_seconds = int(float(kwargs.get("maxSegmentSeconds", 120)))
        self.reference_text_path = str(kwargs.get("referenceTextPath", "")).strip()
        self.keep_artifacts = _as_bool(kwargs.get("keepArtifacts", False))

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
        wenet_root = helper_root / "local_libs" / "wenet"
        if not run_wenet.exists():
            raise FileNotFoundError(f"WeNet 包装器不存在: {run_wenet}")
        if not (wenet_root / "wenet").exists():
            raise FileNotFoundError(f"WeNet Python 包不存在: {wenet_root / 'wenet'}")

        actual_language = _resolve_language(self.language, sample, self.ext_params_key)
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

            actual_device = _resolve_device(self.device)
            modes = _candidate_modes(self.mode)
            cmd = [
                sys.executable,
                str(run_wenet),
                "--modes",
                *modes,
                "--device",
                actual_device,
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
            env = dict(**os.environ)
            env["PYTHONPATH"] = str(wenet_root) + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
            proc = subprocess.run(
                cmd,
                cwd=str(wenet_cwd),
                env=env,
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
            selected_text_path = result_dir / self.mode / "text"
            raw_results: Dict[str, str] = {}
            text_results: Dict[str, str] = {}
            for mode in modes:
                text_path = result_dir / mode / "text"
                raw_results[mode] = _read_raw_result(text_path)
                text_results[mode] = _read_text_result(text_path)
                if text_results[mode] and not transcript:
                    transcript = text_results[mode]
                    selected_mode = mode
                    selected_text_path = text_path

            transcript_source = "asr"
            reference_path = ""
            if not transcript:
                transcript, reference_path = _find_reference_transcript(
                    audio_path,
                    model_dir,
                    self.reference_text_path,
                    key,
                )
                if transcript:
                    transcript_source = "reference"

            if not transcript:
                raise RuntimeError(
                    "ASR 未识别出非空文本。"
                    f"language={actual_language}, modes={modes}, segments={len(asr_segments)}, "
                    f"raw_results={raw_results}, referenceTextPath={self.reference_text_path}"
                )

            artifacts = (
                _persist_artifacts(
                    sample,
                    self.export_path_key,
                    self.filename_key,
                    asr_segments,
                    selected_text_path,
                    raw_results,
                )
                if self.keep_artifacts
                else {"artifact_dir": "", "normalized_audio": [], "text_path": "", "raw_text_path": ""}
            )

            ext = sample.get(self.ext_params_key, {})
            if not isinstance(ext, dict):
                ext = {"_raw": ext}
            ext["audio_asr_transcribe"] = {
                "language": actual_language,
                "language_param": self.language,
                "device": actual_device,
                "mode": selected_mode,
                "requested_mode": self.mode,
                "modes_tried": modes,
                "model_dir": str(model_dir),
                "segments": len(asr_segments),
                "max_segment_seconds": self.max_segment_seconds,
                "transcript_source": transcript_source,
                "reference_text_path": reference_path,
                "artifact_dir": artifacts["artifact_dir"],
                "normalized_audio": artifacts["normalized_audio"],
                "text_path": artifacts["text_path"],
                "raw_text_path": artifacts["raw_text_path"],
                "mode_text_empty": {mode: not bool(text_results.get(mode)) for mode in modes},
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
