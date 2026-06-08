# -- encoding: utf-8 --

from __future__ import annotations

import csv
import json
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Tuple

import numpy as np
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


DEFAULT_AST_CHECKPOINT = "/models/AudioOperations/recog/audioset_10_10_0.4593.pth"


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _resolve_path(value: str, fallback: Path) -> Path:
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


def _strip_sound_marker(stem: str) -> str:
    return re.sub(r"__sound_[A-Za-z0-9._-]+$", "", str(stem or "sample"))


def _mark_sound_filename(sample: Dict[str, Any], filename_key: str, label: str, target_ext: str) -> None:
    file_name = str(sample.get(filename_key) or "").strip()
    stem = _strip_sound_marker(Path(file_name).stem if file_name else "sample")
    sample[filename_key] = f"{stem}__sound_{_safe_marker(label)}.{target_ext}"


def _load_audio_16k(path: Path, sr: int = 16000) -> np.ndarray:
    import librosa  # type: ignore

    audio, _ = librosa.core.load(str(path), sr=sr, mono=True)
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32, copy=False)
    return np.ascontiguousarray(audio)


def _load_audio_16k_mono(path: Path) -> np.ndarray:
    try:
        import soundfile as sf  # type: ignore
        from scipy.signal import resample_poly  # type: ignore

        data, sr = sf.read(str(path), always_2d=True)
        if data.shape[1] > 1:
            data = data.mean(axis=1, keepdims=True)
        wav = data[:, 0]
        if int(sr) != 16000:
            g = np.gcd(int(sr), 16000)
            wav = resample_poly(wav, 16000 // g, int(sr) // g).astype(np.float32, copy=False)
        if wav.dtype != np.float32:
            wav = wav.astype(np.float32, copy=False)
        return np.ascontiguousarray(wav)
    except Exception:
        return _load_audio_16k(path, sr=16000)


@dataclass(frozen=True)
class MacroMap:
    macro_to_labels: Dict[str, List[str]]
    label_to_macro: Dict[str, str]


def _load_macro_map_json(path: Path) -> MacroMap:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"AST 大类映射必须是 JSON object: {path}")
    macro_to_labels: Dict[str, List[str]] = {}
    for macro, labels in obj.items():
        if not isinstance(labels, list):
            raise ValueError(f"AST 大类映射格式错误: {macro}")
        macro_to_labels[str(macro)] = [str(label).strip() for label in labels if str(label).strip()]
    label_to_macro: Dict[str, str] = {}
    for macro, labels in macro_to_labels.items():
        for label in labels:
            label_to_macro[label] = macro
    return MacroMap(macro_to_labels=macro_to_labels, label_to_macro=label_to_macro)


def _load_audioset_labels_csv(csv_path: Path) -> List[str]:
    rows: List[Tuple[int, str]] = []
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append((int(row["index"]), str(row["display_name"]).strip()))
    rows.sort(key=lambda x: x[0])
    labels = [label for _idx, label in rows]
    if not labels:
        raise ValueError(f"AudioSet labels 为空: {csv_path}")
    return labels


_AST_MODEL_CACHE: Dict[Tuple[str, str], Tuple[Any, Any]] = {}


def _cpu_torch_device():
    import torch

    return torch.device("cpu")


def _log_mel_128(wav_16k: np.ndarray) -> np.ndarray:
    import librosa  # type: ignore

    mel = librosa.feature.melspectrogram(
        y=wav_16k,
        sr=16000,
        n_fft=400,
        hop_length=160,
        win_length=400,
        window="hann",
        center=True,
        pad_mode="reflect",
        power=2.0,
        n_mels=128,
        fmin=0,
        fmax=8000,
    )
    log_mel = np.log(mel + 1e-10).T
    if log_mel.dtype != np.float32:
        log_mel = log_mel.astype(np.float32, copy=False)
    return np.ascontiguousarray(log_mel)


def _audioset_norm(spec: np.ndarray) -> np.ndarray:
    return (spec + 4.26) / (4.57 * 2.0)


def _sliding_windows(wav: np.ndarray, *, segment_sec: float, hop_sec: float) -> Iterable[np.ndarray]:
    seg_len = int(round(float(segment_sec) * 16000))
    hop_len = int(round(float(hop_sec) * 16000))
    if seg_len <= 0:
        raise ValueError("segment_sec 必须大于 0")
    if hop_len <= 0:
        hop_len = seg_len
    n = int(wav.shape[0])
    if n <= seg_len:
        pad = seg_len - n
        yield np.pad(wav, (0, pad), mode="constant") if pad > 0 else wav
        return
    start = 0
    while start < n:
        end = start + seg_len
        if end <= n:
            yield wav[start:end]
        else:
            yield np.pad(wav[start:n], (0, end - n), mode="constant")
        if end >= n:
            break
        start += hop_len


MacroAgg = Literal["max", "sum"]


def _macro_scores_from_probs(labels: List[str], probs: np.ndarray, macro_map: MacroMap, macro_agg: MacroAgg) -> Dict[str, float]:
    name_to_idx = {name: i for i, name in enumerate(labels)}
    scores: Dict[str, float] = {}
    for macro, names in macro_map.macro_to_labels.items():
        idxs = [name_to_idx[name] for name in names if name in name_to_idx]
        if not idxs:
            scores[macro] = 0.0
            continue
        vals = probs[idxs]
        scores[macro] = float(np.sum(vals)) if macro_agg == "sum" else float(np.max(vals))
    return scores


def _topk_labels(labels: List[str], probs: np.ndarray, k: int, label_to_macro: Dict[str, str]) -> List[Dict[str, object]]:
    topk = max(1, min(int(k), len(labels)))
    idx = np.argsort(probs)[::-1][:topk]
    return [
        {
            "label": str(labels[i]),
            "macro_class": label_to_macro.get(str(labels[i]), "Other"),
            "prob": round(float(probs[i]), 8),
        }
        for i in idx
    ]


def _load_ast_model(checkpoint_path: Path, labels_count: int, device):
    cache_key = (str(checkpoint_path), str(device))
    if cache_key in _AST_MODEL_CACHE:
        return _AST_MODEL_CACHE[cache_key]
    try:
        from .ast_vendor import ASTConfig, load_ast_from_pth  # type: ignore
    except ImportError:
        from ast_vendor import ASTConfig, load_ast_from_pth  # type: ignore

    cfg = ASTConfig(label_dim=int(labels_count), input_fdim=128, input_tdim=1024, fstride=10, tstride=10, model_size="base384")
    model = load_ast_from_pth(checkpoint_path=str(checkpoint_path), device=device, cfg=cfg)
    _AST_MODEL_CACHE[cache_key] = (model, device)
    return model, device


def _infer_ast(
    audio_path: Path,
    checkpoint_path: Path,
    labels_csv: Path,
    macro_map_path: Path,
    topk: int,
    segment_sec: float,
    hop_sec: float,
    macro_agg: MacroAgg,
) -> Dict[str, Any]:
    import torch

    labels = _load_audioset_labels_csv(labels_csv)
    macro_map = _load_macro_map_json(macro_map_path)
    device = _cpu_torch_device()
    model, device = _load_ast_model(checkpoint_path, len(labels), device)
    wav = _load_audio_16k_mono(audio_path)

    macro_scores_sum: Dict[str, float] = {}
    probs_sum = None
    probs_n = 0
    segment_count = 0
    for seg_wav in _sliding_windows(wav, segment_sec=float(segment_sec), hop_sec=float(hop_sec)):
        spec = _audioset_norm(_log_mel_128(seg_wav))
        if spec.shape[0] < 1024:
            spec = np.pad(spec, ((0, 1024 - int(spec.shape[0])), (0, 0)), mode="constant")
        else:
            spec = spec[:1024, :]
        x = torch.from_numpy(spec).unsqueeze(0).to(device=device, dtype=torch.float32)
        with torch.inference_mode():
            logits = model(x)[0]
            probs = torch.sigmoid(logits).detach().cpu().to(torch.float32).numpy()
        scores = _macro_scores_from_probs(labels, probs, macro_map, macro_agg=macro_agg)
        for key, value in scores.items():
            macro_scores_sum[key] = macro_scores_sum.get(key, 0.0) + float(value)
        probs_sum = probs.astype(np.float64, copy=True) if probs_sum is None else probs_sum + probs
        probs_n += 1
        segment_count += 1

    if probs_sum is None or probs_n <= 0:
        raise RuntimeError("AST 分类未产生有效分段概率")
    macro_scores = {key: value / float(probs_n) for key, value in macro_scores_sum.items()}
    pred_macro = max(macro_scores, key=lambda k: macro_scores[k]) if macro_scores else "Noise"
    probs_mean = (probs_sum / float(probs_n)).astype(np.float32, copy=False)
    return {
        "macro_class": pred_macro,
        "macro_scores": {k: round(float(v), 8) for k, v in macro_scores.items()},
        "small_topk": _topk_labels(labels, probs_mean, topk, macro_map.label_to_macro),
        "model": "AST AudioSet 10_10_0.4593",
        "checkpoint": str(checkpoint_path),
        "macro_map": str(macro_map_path),
        "labels_csv": str(labels_csv),
        "device": str(device),
        "segments": segment_count,
        "segment_sec": float(segment_sec),
        "hop_sec": float(hop_sec),
        "macro_agg": macro_agg,
    }


class AudioSoundClassify(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend = "ast"
        self.ast_checkpoint = str(kwargs.get("astCheckpoint") or DEFAULT_AST_CHECKPOINT).strip()
        self.ast_macro_map = str(kwargs.get("astMacroMap", "")).strip()
        self.labels_csv = str(kwargs.get("labelsCsv", "")).strip()
        self.topk = int(float(kwargs.get("topK", 10)))
        self.segment_sec = float(kwargs.get("segmentSeconds", 10.24))
        self.hop_sec = float(kwargs.get("hopSeconds", 5.12))
        self.macro_agg = str(kwargs.get("macroAgg", "max")).strip().lower()

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

        package_root = _package_root()

        data = sample.get(self.data_key)
        audio_bytes = b""
        with tempfile.TemporaryDirectory(prefix="dm_audio_sound_classify_") as td:
            work_dir = Path(td)
            if isinstance(data, (bytes, bytearray)) and data:
                audio_bytes = bytes(data)
                audio_path = work_dir / f"input.{_audio_ext(sample)}"
                audio_path.write_bytes(audio_bytes)
            else:
                audio_path = Path(str(sample.get(self.filepath_key, ""))).expanduser().resolve()
                if not audio_path.exists():
                    raise FileNotFoundError(f"输入音频不存在: {audio_path}")
                if self.is_last_op:
                    audio_bytes = audio_path.read_bytes()
            audio_path_for_infer = audio_path

            checkpoint_path = _resolve_path(self.ast_checkpoint, Path(DEFAULT_AST_CHECKPOINT))
            labels_csv = _resolve_path(
                self.labels_csv,
                package_root / "models" / "recog" / "class_labels_indices.csv",
            )
            macro_map_path = _resolve_path(
                self.ast_macro_map,
                package_root / "models" / "recog" / "audioset_macro_map_v1.json",
            )
            if not checkpoint_path.exists():
                raise FileNotFoundError(f"AST 分类模型不存在: {checkpoint_path}")
            if not labels_csv.exists():
                raise FileNotFoundError(f"AudioSet labels CSV 不存在: {labels_csv}")
            if not macro_map_path.exists():
                raise FileNotFoundError(f"AST 大类映射不存在: {macro_map_path}")
            if self.macro_agg not in {"max", "sum"}:
                raise ValueError(f"不支持的 macroAgg: {self.macro_agg}")
            result_core = _infer_ast(
                audio_path_for_infer,
                checkpoint_path,
                labels_csv,
                macro_map_path,
                self.topk,
                self.segment_sec,
                self.hop_sec,
                self.macro_agg,  # type: ignore[arg-type]
            )

        key = _sample_key(sample, audio_path, self.filename_key)
        result = {
            "key": key,
            "backend": self.backend,
            **result_core,
        }

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_sound_classify"] = result
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
        _mark_sound_filename(sample, self.filename_key, str(result.get("macro_class") or "unknown"), target_ext)

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioSoundClassify costs {time.time() - start:6f} s"
        )
        return sample
