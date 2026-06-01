# -- encoding: utf-8 --

from __future__ import annotations

import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Tuple

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


DEFAULT_HF_MODEL_DIR = "/models/AudioOperations/emotion/new_model"
DEFAULT_SMALL_CHECKPOINT = "/models/AudioOperations/emotion/small_model.safetensors"


def _package_root() -> Path:
    return Path(__file__).resolve().parent


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


def _safe_marker(value: str, default: str = "unknown") -> str:
    marker = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or default)).strip("._-")
    return marker[:80] or default


def _strip_emotion_marker(stem: str) -> str:
    return re.sub(r"__emotion_[A-Za-z0-9._-]+$", "", str(stem or "sample"))


def _mark_emotion_filename(sample: Dict[str, Any], filename_key: str, label: str, target_ext: str) -> None:
    file_name = str(sample.get(filename_key) or "").strip()
    stem = _strip_emotion_marker(Path(file_name).stem if file_name else "sample")
    sample[filename_key] = f"{stem}__emotion_{_safe_marker(label)}.{target_ext}"


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


def _detect_device(device_arg: str):
    import torch

    dev = str(device_arg or "auto").strip().lower()
    if dev == "cpu":
        return torch.device("cpu")
    if dev == "cuda":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if dev == "npu":
        try:
            import torch_npu  # type: ignore  # noqa: F401
            return torch.device("npu")
        except Exception:
            return torch.device("privateuseone")
    if dev == "auto":
        try:
            import torch_npu  # type: ignore  # noqa: F401
            try:
                return torch.device("npu")
            except Exception:
                return torch.device("privateuseone")
        except Exception:
            if torch.cuda.is_available():
                return torch.device("cuda")
            return torch.device("cpu")
    raise ValueError(f"不支持的情感识别设备: {device_arg}")


_HF_CACHE: Dict[Tuple[str, str], Tuple[Any, Any]] = {}
_SMALL_CACHE: Dict[Tuple[str, str], Any] = {}


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


def _load_small_model(checkpoint: Path, device):
    cache_key = (str(checkpoint), str(device))
    if cache_key in _SMALL_CACHE:
        return _SMALL_CACHE[cache_key]
    utils_dir = _package_root() / "helpers" / "utils"
    if str(utils_dir) not in sys.path:
        sys.path.insert(0, str(utils_dir))
    from emotion_small_model import load_small_model_from_safetensors  # type: ignore

    model = load_small_model_from_safetensors(checkpoint, device=device)
    _SMALL_CACHE[cache_key] = model
    return model


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


def _predict_small(model, wav_16k, device) -> Tuple[str, float, Dict[str, float]]:
    import torch

    labels = ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"]
    with torch.inference_mode():
        logits = model(input_values=wav_16k.unsqueeze(0).to(device))
        probs = torch.softmax(logits, dim=-1)[0]
        pred_id = int(torch.argmax(probs).item())
        score = float(probs[pred_id].detach().cpu().item())
        distribution = {labels[i]: round(float(probs[i].detach().cpu().item()), 8) for i in range(len(labels))}
        return labels[pred_id], score, distribution


class AudioEmotionRecognize(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = str(kwargs.get("backend", "hf")).strip().lower()
        self.hf_model_dir = str(kwargs.get("hfModelDir", DEFAULT_HF_MODEL_DIR)).strip()
        self.small_checkpoint = str(kwargs.get("smallCheckpoint", DEFAULT_SMALL_CHECKPOINT)).strip()
        self.device = str(kwargs.get("device", "auto")).strip().lower()
        self.keep_audio = str(kwargs.get("keepAudio", "true")).strip().lower() in {"1", "true", "yes", "y", "on"}

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

        device = _detect_device(self.device)
        data = sample.get(self.data_key)
        audio_bytes = b""
        with tempfile.TemporaryDirectory(prefix="dm_audio_emotion_") as td:
            work_dir = Path(td)
            if isinstance(data, (bytes, bytearray)) and data:
                audio_bytes = bytes(data)
                audio_path = work_dir / f"input.{_audio_ext(sample)}"
                audio_path.write_bytes(audio_bytes)
            else:
                audio_path = Path(str(sample.get(self.filepath_key, ""))).expanduser().resolve()
                if not audio_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {audio_path}")
                if self.keep_audio or self.is_last_op:
                    audio_bytes = audio_path.read_bytes()
            wav = _load_wav_16k_mono(audio_path)

        backend = self.backend
        if backend not in {"hf", "small"}:
            raise ValueError(f"不支持的情感识别后端: {self.backend}")
        if backend == "small":
            checkpoint = _resolve_model_dir(self.small_checkpoint, Path(DEFAULT_SMALL_CHECKPOINT))
            if not checkpoint.exists():
                raise FileNotFoundError(f"情感识别 small checkpoint 不存在: {checkpoint}")
            model = _load_small_model(checkpoint, device)
            pred_en, score, distribution = _predict_small(model, wav, device)
            model_path = str(checkpoint)
        else:
            model_dir = _resolve_model_dir(self.hf_model_dir, Path(DEFAULT_HF_MODEL_DIR))
            if not model_dir.exists():
                raise FileNotFoundError(f"情感识别 HF 模型目录不存在: {model_dir}")
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
            "backend": backend,
            "model_path": model_path,
            "device": str(device),
        }

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_emotion_recognize"] = result
        sample[self.ext_params_key] = ext

        target_ext = _audio_ext(sample)
        if audio_bytes:
            sample[self.data_key] = audio_bytes
        sample[self.text_key] = ""
        if self.is_last_op:
            sample[self.filetype_key] = "txt"
            sample[self.target_type_key] = target_ext
        else:
            sample[self.filetype_key] = target_ext
            sample[self.target_type_key] = target_ext
        _mark_emotion_filename(sample, self.filename_key, str(result.get("pred_en") or "unknown"), target_ext)

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioEmotionRecognize costs {time.time() - start:6f} s"
        )
        return sample
