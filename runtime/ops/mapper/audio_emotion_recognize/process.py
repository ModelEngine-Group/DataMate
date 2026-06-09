# -- encoding: utf-8 --

from __future__ import annotations

import fcntl
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)

from datamate.core.base_op import Mapper
try:
    from .audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample
except ImportError:
    from audio_skip import invalid_quality_reason, is_audio_sample, mark_skipped_sample


DEFAULT_HF_MODEL_DIR = "/models/AudioOperations/emotion/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
DEFAULT_EMOTION_REPORT_PATH = "/dataset/{dataset_id}/references/emotion_recognition.jsonl"
EMOTION_LOCK_DIR = Path("/tmp/datamate_audio_emotion_recognize_locks")


def _as_bool(v: object) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on", "保存", "文本"}


def _resolve_model_dir(value: str, fallback: Path) -> Path:
    raw = str(value or "").strip()
    if raw:
        p = Path(raw).expanduser()
        if p.exists():
            return p.resolve()
    return fallback.resolve()


def _audio_ext(sample: Dict[str, Any], default_ext: str = "wav") -> str:
    ext = str(sample.get("target_type") or sample.get("fileType") or default_ext).strip().lower().lstrip(".")
    return ext or default_ext


def _sample_key(sample: Dict[str, Any], audio_path: Path, filename_key: str) -> str:
    file_name = str(sample.get(filename_key) or "").strip()
    if file_name:
        return Path(file_name).stem or audio_path.stem
    return audio_path.stem


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


def _default_emotion_report_path(sample: Dict[str, Any]) -> Path:
    export_path = str(sample.get("export_path") or "").strip()
    if export_path:
        return Path(export_path).expanduser() / "references" / "emotion_recognition.jsonl"

    dataset_id = str(sample.get("dataset_id") or sample.get("datasetId") or "").strip()
    if dataset_id:
        return Path("/dataset") / dataset_id / "references" / "emotion_recognition.jsonl"

    file_path = str(sample.get("filePath") or "")
    dataset_root = _dataset_root_from_audio_path(file_path)
    if str(dataset_root) not in {"", "."}:
        return dataset_root / "references" / "emotion_recognition.jsonl"

    return Path("/dataset") / "references" / "emotion_recognition.jsonl"


def _resolve_emotion_report_path(path_value: str, sample: Dict[str, Any]) -> Path:
    raw_value = str(path_value or DEFAULT_EMOTION_REPORT_PATH).strip()
    expanded = _expand_dataset_placeholders(raw_value, sample)
    if not expanded:
        return _default_emotion_report_path(sample)
    if raw_value == DEFAULT_EMOTION_REPORT_PATH and sample.get("export_path"):
        return _default_emotion_report_path(sample)
    if _has_unresolved_dataset_placeholder(expanded):
        return _default_emotion_report_path(sample)

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


def _emotion_record_keys(row: Dict[str, Any]) -> Set[str]:
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
    return row, _emotion_record_keys(row)


def _upsert_emotion_report(path: Path, file_name: str, result: Dict[str, Any]) -> None:
    file_name = Path(file_name).name
    record = dict(result)
    record.update(
        {
            "file": file_name,
            "fileName": file_name,
            "key": Path(file_name).stem,
        }
    )
    record_keys = _emotion_record_keys(record)
    lock_name = hashlib.sha1(str(path).encode("utf-8")).hexdigest() + ".lock"
    EMOTION_LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = EMOTION_LOCK_DIR / lock_name

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


def _load_wav_16k_mono(path: Path):
    try:
        import numpy as np
        import soundfile as sf  # type: ignore
        from scipy.signal import resample_poly  # type: ignore
        import torch

        data, sr = sf.read(str(path), always_2d=True)
        if data.shape[1] > 1:
            data = data.mean(axis=1, keepdims=True)
        wav = data[:, 0]
        if int(sr) != 16000:
            g = np.gcd(int(sr), 16000)
            wav = resample_poly(wav, 16000 // g, int(sr) // g).astype("float32", copy=False)
        if wav.dtype != np.float32:
            wav = wav.astype("float32", copy=False)
        return torch.from_numpy(wav).contiguous()
    except Exception:
        import torch
        import torchaudio  # type: ignore

        wav, sr = torchaudio.load(str(path))
        if wav.ndim == 2 and wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        if int(sr) != 16000:
            wav = torchaudio.functional.resample(wav, int(sr), 16000)
        wav = wav.squeeze(0).contiguous()
        return wav.to(torch.float32) if wav.dtype != torch.float32 else wav


def _cpu_device():
    import torch

    return torch.device("cpu")


_HF_CACHE: Dict[Tuple[str, str], Tuple[Any, Any]] = {}


def _load_hf_model(model_dir: Path, device):
    cache_key = (str(model_dir), str(device))
    if cache_key in _HF_CACHE:
        return _HF_CACHE[cache_key]

    from transformers import AutoConfig, AutoFeatureExtractor, AutoModelForAudioClassification  # type: ignore

    feature_extractor = AutoFeatureExtractor.from_pretrained(str(model_dir), local_files_only=True)
    safetensors_path = model_dir / "model.safetensors"
    cfg = AutoConfig.from_pretrained(str(model_dir), local_files_only=True)
    if safetensors_path.exists():
        from safetensors.torch import load_file  # type: ignore

        state = load_file(str(safetensors_path), device="cpu")
        if "classifier.dense.weight" in state:
            setattr(cfg, "classifier_proj_size", int(state["classifier.dense.weight"].shape[0]))
        if "classifier.output.weight" in state:
            cfg.num_labels = int(state["classifier.output.weight"].shape[0])
        model = AutoModelForAudioClassification.from_config(cfg)
        if "classifier.dense.weight" in state and "projector.weight" not in state:
            remap = {
                "classifier.dense.weight": "projector.weight",
                "classifier.dense.bias": "projector.bias",
                "classifier.output.weight": "classifier.weight",
                "classifier.output.bias": "classifier.bias",
            }
            for old_key, new_key in remap.items():
                if old_key in state and new_key not in state:
                    state[new_key] = state[old_key]
        model.load_state_dict(state, strict=False)
    else:
        model = AutoModelForAudioClassification.from_pretrained(str(model_dir), local_files_only=True)
    model.eval()
    model.to(device)
    _HF_CACHE[cache_key] = (model, feature_extractor)
    return model, feature_extractor


def _zh_mapping() -> Dict[str, str]:
    return {
        "happy": "喜",
        "angry": "怒",
        "sad": "哀",
        "fearful": "惧",
        "disgust": "厌",
        "surprised": "惊",
        "neutral": "中",
        "calm": "困惑",
    }


def _predict_hf(model, feature_extractor, wav_16k, device) -> Tuple[str, float, Dict[str, float]]:
    import torch

    with torch.inference_mode():
        inputs = feature_extractor(
            wav_16k.detach().cpu().numpy(),
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        out = model(**inputs)
        probs = torch.softmax(out.logits[0], dim=-1)
        pred_id = int(torch.argmax(probs).item())
        score = float(probs[pred_id].detach().cpu().item())
        id2label = getattr(model.config, "id2label", None) or {}
        label = id2label.get(pred_id) if isinstance(id2label, dict) else None
        if label is None:
            label = id2label.get(str(pred_id)) if isinstance(id2label, dict) else None
        labels = []
        for i in range(int(probs.numel())):
            label_i = id2label.get(i) if isinstance(id2label, dict) else None
            if label_i is None and isinstance(id2label, dict):
                label_i = id2label.get(str(i))
            labels.append(str(label_i or i).lower())
        distribution = {labels[i]: round(float(probs[i].detach().cpu().item()), 8) for i in range(len(labels))}
        return str(label or pred_id).lower(), score, distribution


class AudioEmotionRecognize(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hf_model_dir = str(kwargs.get("hfModelDir", DEFAULT_HF_MODEL_DIR)).strip()
        self.save_as_text = _as_bool(kwargs.get("saveAsText", True))
        self.result_report_path = str(
            kwargs.get("resultSavePath", kwargs.get("resultReportPath", DEFAULT_EMOTION_REPORT_PATH))
        ).strip()

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

        device = _cpu_device()
        data = sample.get(self.data_key)
        audio_bytes = b""
        with tempfile.TemporaryDirectory(prefix="dm_audio_emotion_") as td:
            work_dir = Path(td)
            if isinstance(data, (bytes, bytearray)) and data:
                raw_audio_bytes = bytes(data)
                audio_path = work_dir / f"input.{_audio_ext(sample)}"
                audio_path.write_bytes(raw_audio_bytes)
                if self.is_last_op:
                    audio_bytes = raw_audio_bytes
            else:
                audio_path = Path(str(sample.get(self.filepath_key, ""))).expanduser().resolve()
                if not audio_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {audio_path}")
                if self.is_last_op:
                    audio_bytes = audio_path.read_bytes()
            wav = _load_wav_16k_mono(audio_path)

        model_dir = _resolve_model_dir(self.hf_model_dir, Path(DEFAULT_HF_MODEL_DIR))
        if not model_dir.exists():
            raise FileNotFoundError(f"情感识别模型目录不存在: {model_dir}")
        model, feature_extractor = _load_hf_model(model_dir, device)
        pred_en, score, distribution = _predict_hf(model, feature_extractor, wav, device)
        model_path = str(model_dir)

        pred_zh = _zh_mapping().get(pred_en, pred_en)
        key = _sample_key(sample, Path(str(sample.get(self.filepath_key, "sample"))), self.filename_key)
        result = {
            "key": key,
            "pred_en": pred_en,
            "pred_zh": pred_zh,
            "score": round(float(score), 8),
            "distribution": distribution,
            "model_path": model_path,
            "device": str(device),
        }
        source_file_name = _source_file_name(sample, self.filename_key, self.filepath_key)
        result_report_file = ""
        if not self.save_as_text:
            report_path = _resolve_emotion_report_path(self.result_report_path, sample)
            _upsert_emotion_report(report_path, source_file_name, result)
            result_report_file = str(report_path)
            result["result_report_file"] = result_report_file

        ext_raw = sample.get(self.ext_params_key, {})
        if isinstance(ext_raw, dict):
            ext = dict(ext_raw)
        else:
            ext = {"_raw": ext}
        ext["audio_emotion_recognize"] = result
        sample[self.ext_params_key] = ext

        target_ext = _audio_ext(sample)
        if self.save_as_text:
            sample[self.text_key] = pred_en
            sample[self.data_key] = b""
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = "txt"
        else:
            if self.is_last_op and audio_bytes:
                sample[self.data_key] = audio_bytes
            else:
                sample[self.data_key] = b""
            sample[self.text_key] = ""
            if self.is_last_op:
                sample[self.filetype_key] = "txt"
                sample[self.target_type_key] = target_ext
            else:
                sample[self.filetype_key] = target_ext
                sample[self.target_type_key] = target_ext

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioEmotionRecognize "
            f"save_as_text={self.save_as_text}, pred={pred_en}, report={result_report_file}, "
            f"costs {time.time() - start:6f} s"
        )
        return sample
