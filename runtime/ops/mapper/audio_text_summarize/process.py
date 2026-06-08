# -- encoding: utf-8 --

from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
try:
    from loguru import logger
except Exception:
    import logging

    logger = logging.getLogger(__name__)

from datamate.core.base_op import Mapper


DEFAULT_ONNX_MODEL_DIR = "/models/AudioOperations/summary/summary-model"
_RE_CJK = re.compile(r"[\u4e00-\u9fff]")
_RE_EN_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
_EN_STOP = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "so", "as", "at", "by", "for", "from",
    "in", "into", "of", "on", "onto", "out", "over", "to", "up", "with", "without", "about", "after",
    "before", "between", "during", "through", "under", "again", "once", "here", "there", "when", "where",
    "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "than", "too", "very", "can", "will", "just", "should", "now",
    "i", "me", "my", "we", "us", "our", "you", "your", "he", "him", "his", "she", "her", "they", "them",
    "their", "it", "its", "this", "that", "these", "those", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did",
}


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _limit_cpu_threads(n: int) -> None:
    s = str(max(1, int(n)))
    for key in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[key] = s


def _detect_lang(text: str) -> str:
    return "zh" if _RE_CJK.search(text or "") else "en"


def _clean_en(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _clean_zh(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").strip())


def _en_tokens(text: str) -> List[str]:
    return [m.group(0) for m in _RE_EN_WORD.finditer(text or "")]


def _idf(n_docs: int, df: int) -> float:
    return float(math.log((n_docs + 1.0) / (df + 1.0)) + 1.0)


def _single_doc_en_idf(text: str) -> Dict[str, float]:
    toks = {w.lower() for w in _en_tokens(text) if w}
    return {w: _idf(1, 1) for w in toks}


def _single_doc_zh_idf(text: str) -> Dict[str, float]:
    try:
        import jieba  # type: ignore

        toks = {tok for tok in jieba.lcut(_clean_zh(text)) if tok and tok.strip()}
    except Exception:
        toks = set(_clean_zh(text))
    return {w: _idf(1, 1) for w in toks}


def _best_en_window(text: str, *, min_words: int, max_words: int) -> str:
    s = _clean_en(text)
    words = _en_tokens(s)
    if not words:
        return ""
    max_words = int(max_words)
    if max_words <= 0 or len(words) <= max_words:
        return " ".join(words)
    min_words = max(1, min(int(min_words), max_words))
    idf_map = _single_doc_en_idf(s)
    weights: List[float] = []
    for w in words:
        wl = w.lower()
        if wl in _EN_STOP or len(wl) <= 1:
            weights.append(0.0)
        else:
            weights.append(float(idf_map.get(wl, 1.0)))
    pref = [0.0]
    for x in weights:
        pref.append(pref[-1] + x)
    best = (0, min(max_words, len(words)))
    best_score = -1.0
    for length in range(min_words, max_words + 1):
        if length > len(words):
            break
        for start in range(0, len(words) - length + 1):
            score = pref[start + length] - pref[start]
            density = score / float(length)
            combined = score + 0.15 * density
            if combined > best_score:
                best_score = combined
                best = (start, start + length)
    return " ".join(words[best[0] : best[1]]).strip()


def _best_zh_window(text: str, *, max_chars: int) -> str:
    s = _clean_zh(text)
    if not s:
        return ""
    max_chars = int(max_chars)
    if max_chars <= 0 or len(s) <= max_chars:
        return s
    idf_map = _single_doc_zh_idf(s)
    scores = [0.0] * len(s)
    try:
        import jieba  # type: ignore

        spans = list(jieba.tokenize(s))
        for tok, start, end in spans:
            t = (tok or "").strip()
            if not t:
                continue
            weight = float(idf_map.get(t, 1.0))
            if len(t) == 1:
                weight *= 0.25
            for pos in range(max(0, start), min(len(s), end)):
                scores[pos] += weight
    except Exception:
        for i, ch in enumerate(s):
            scores[i] = 0.25 if ch in "的一是在和了有就不人都" else 1.0
    pref = [0.0]
    for x in scores:
        pref.append(pref[-1] + x)
    best_start = 0
    best_score = -1.0
    for start in range(0, len(s) - max_chars + 1):
        score = pref[start + max_chars] - pref[start]
        if score > best_score:
            best_score = score
            best_start = start
    return s[best_start : best_start + max_chars].strip()


def _truncate_summary(summary: str, lang: str, max_chars_zh: int, max_words_en: int) -> str:
    if lang == "zh":
        s = _clean_zh(summary)
        return s[: int(max_chars_zh)].strip() if int(max_chars_zh) > 0 else s
    words = _en_tokens(summary)
    if int(max_words_en) > 0:
        words = words[: int(max_words_en)]
    return " ".join(words).strip()


def _extractive_summary(text: str, max_chars_zh: int, max_words_en: int, min_words_en: int) -> Tuple[str, str]:
    lang = _detect_lang(text)
    if lang == "zh":
        return _best_zh_window(text, max_chars=int(max_chars_zh)), lang
    return _best_en_window(text, min_words=int(min_words_en), max_words=int(max_words_en)), lang


def _parse_keyed_lines(text: str, mode: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    lines = [line.rstrip("\n") for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return []
    actual_mode = str(mode or "single").strip().lower()
    if actual_mode == "single":
        return [("", text.strip())]
    if actual_mode == "auto":
        if not all("\t" in line for line in lines):
            return [("", text.strip())]
        actual_mode = "tab"
    for idx, line in enumerate(lines):
        if actual_mode == "tab" and "\t" in line:
            key, value = line.split("\t", 1)
        elif actual_mode == "space":
            parts = line.strip().split(maxsplit=1)
            key = parts[0] if parts else str(idx)
            value = parts[1] if len(parts) > 1 else ""
        else:
            key, value = str(idx), line
        rows.append((key.strip(), value.strip()))
    return rows


def _mark_skipped_text_sample(sample: Dict[str, Any], reason: str, op_name: str, keys: Tuple[str, ...]) -> Dict[str, Any]:
    text_key, data_key, filetype_key, target_type_key, ext_params_key = keys
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


def _read_text_from_sample(sample: Dict[str, Any], text_key: str, filepath_key: str, filetype_key: str) -> str:
    text = str(sample.get(text_key) or "")
    if text.strip():
        return text
    file_type = str(sample.get(filetype_key) or "").strip().lower().lstrip(".")
    path_value = str(sample.get(filepath_key) or "").strip()
    if file_type in {"txt", "text", "md", "json", "jsonl"} and path_value:
        path = Path(path_value).expanduser().resolve()
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="ignore")
    return ""


def _resolve_onnx_model_dir(value: str) -> Path:
    raw = str(value or "").strip() or DEFAULT_ONNX_MODEL_DIR
    path = Path(raw).expanduser()
    if path.exists():
        return path.resolve()
    bundled = Path(__file__).resolve().parent / "models" / "summary-model"
    if bundled.exists():
        return bundled.resolve()
    return path.resolve()


def _available_providers() -> List[str]:
    try:
        import onnxruntime as ort  # type: ignore

        return list(ort.get_available_providers())
    except Exception:
        return []


def _pick_providers(provider_arg: str) -> List[str]:
    requested = [p.strip() for p in str(provider_arg or "").split(",") if p.strip()]
    if not requested:
        requested = ["CANNExecutionProvider", "CPUExecutionProvider"]
    available = set(_available_providers())
    picked = [p for p in requested if p in available]
    return picked or ["CPUExecutionProvider"]


_ONNX_CACHE: Dict[Tuple[str, str], Tuple[Any, Any, List[str]]] = {}


def _load_onnx_embedder(model_dir: Path, providers: Sequence[str], cpu_threads: int):
    cache_key = (str(model_dir), ",".join(providers))
    if cache_key in _ONNX_CACHE:
        return _ONNX_CACHE[cache_key]

    import onnxruntime as ort  # type: ignore
    from transformers import AutoTokenizer  # type: ignore

    model_path = model_dir / "model.onnx"
    if not model_path.exists():
        raise FileNotFoundError(f"摘要 ONNX 模型不存在: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = int(cpu_threads)
    opts.inter_op_num_threads = 1
    session = ort.InferenceSession(str(model_path), sess_options=opts, providers=list(providers))
    used = list(session.get_providers())
    _ONNX_CACHE[cache_key] = (tokenizer, session, used)
    return tokenizer, session, used


def _mean_pool(last_hidden: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    mask = attention_mask.astype(np.float32)
    if last_hidden.ndim == 2:
        return last_hidden[0].astype(np.float32)
    masked = last_hidden * mask[:, :, None]
    denom = np.maximum(mask.sum(axis=1, keepdims=True), 1e-8)
    return (masked.sum(axis=1) / denom)[0].astype(np.float32)


def _embed_texts(texts: Sequence[str], model_dir: Path, providers: Sequence[str], cpu_threads: int) -> Tuple[List[np.ndarray], List[str]]:
    tokenizer, session, used = _load_onnx_embedder(model_dir, providers, cpu_threads)
    out: List[np.ndarray] = []
    input_names = {inp.name for inp in session.get_inputs()}
    for text in texts:
        enc = tokenizer(
            text,
            return_tensors="np",
            truncation=True,
            max_length=512,
            padding=True,
        )
        feeds: Dict[str, np.ndarray] = {}
        for name in input_names:
            if name in enc:
                feeds[name] = enc[name].astype(np.int64)
            elif name == "token_type_ids":
                feeds[name] = np.zeros_like(enc["input_ids"], dtype=np.int64)
        result = session.run(None, feeds)
        vec = _mean_pool(np.asarray(result[0]), np.asarray(enc["attention_mask"]))
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        out.append(vec)
    return out, used


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _candidate_windows(text: str, lang: str, max_chars_zh: int, max_words_en: int, max_windows: int) -> List[str]:
    if lang == "zh":
        s = _clean_zh(text)
        if not s:
            return []
        size = max(8, int(max_chars_zh))
        stride = max(1, size // 2)
        if len(s) <= size:
            return [s]
        windows = [s[i : i + size] for i in range(0, max(1, len(s) - size + 1), stride)]
        if windows and windows[-1] != s[-size:]:
            windows.append(s[-size:])
        return windows[: max(1, int(max_windows))]

    words = _en_tokens(text)
    if not words:
        return []
    size = max(4, int(max_words_en))
    stride = max(1, size // 2)
    if len(words) <= size:
        return [" ".join(words)]
    windows = [" ".join(words[i : i + size]) for i in range(0, max(1, len(words) - size + 1), stride)]
    tail = " ".join(words[-size:])
    if windows and windows[-1] != tail:
        windows.append(tail)
    return windows[: max(1, int(max_windows))]


def _onnx_extractive_summary(
    text: str,
    *,
    model_dir: Path,
    providers: Sequence[str],
    cpu_threads: int,
    max_chars_zh: int,
    max_words_en: int,
    max_windows: int,
) -> Tuple[str, str, Dict[str, Any]]:
    lang = _detect_lang(text)
    windows = _candidate_windows(text, lang, max_chars_zh, max_words_en, max_windows)
    if not windows:
        return "", lang, {"providers": list(providers), "windows": 0}
    vectors, used = _embed_texts([text, *windows], model_dir, providers, cpu_threads)
    query = vectors[0]
    candidates = vectors[1:]
    best_idx = max(range(len(candidates)), key=lambda i: _cosine(query, candidates[i]))
    summary = _truncate_summary(windows[best_idx], lang, max_chars_zh, max_words_en)
    return summary, lang, {"providers": used, "windows": len(windows), "selected_window": int(best_idx)}


class AudioTextSummarize(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.method = str(kwargs.get("method", "extractive")).strip().lower()
        self.max_chars_zh = int(float(kwargs.get("maxSummaryCharsZh", 40)))
        self.max_words_en = int(float(kwargs.get("maxSummaryWordsEn", 18)))
        self.min_words_en = int(float(kwargs.get("minSummaryWordsEn", 8)))
        self.line_mode = str(kwargs.get("lineMode", "single")).strip().lower()
        self.preserve_keys = _as_bool(kwargs.get("preserveKeys", True))
        self.onnx_model_dir = str(kwargs.get("onnxModelDir", DEFAULT_ONNX_MODEL_DIR)).strip()
        self.providers_priority = str(kwargs.get("providersPriority", "CANNExecutionProvider,CPUExecutionProvider")).strip()
        self.cpu_threads = int(float(kwargs.get("cpuThreads", 4)))
        self.max_windows = int(float(kwargs.get("maxWindows", 96)))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        text = _read_text_from_sample(sample, self.text_key, self.filepath_key, self.filetype_key)
        if not text.strip():
            return _mark_skipped_text_sample(
                sample,
                "empty_text_for_summary",
                self.__class__.__name__,
                (self.text_key, self.data_key, self.filetype_key, self.target_type_key, self.ext_params_key),
            )

        _limit_cpu_threads(self.cpu_threads)
        rows = _parse_keyed_lines(text, self.line_mode)
        summaries: List[Tuple[str, str, str, Dict[str, Any]]] = []
        method = self.method
        if method not in {"extractive", "bert_onnx"}:
            raise ValueError(f"不支持的文本概括方法: {self.method}")

        for key, row_text in rows:
            if method == "bert_onnx":
                model_dir = _resolve_onnx_model_dir(self.onnx_model_dir)
                providers = _pick_providers(self.providers_priority)
                summary, lang, meta = _onnx_extractive_summary(
                    row_text,
                    model_dir=model_dir,
                    providers=providers,
                    cpu_threads=self.cpu_threads,
                    max_chars_zh=self.max_chars_zh,
                    max_words_en=self.max_words_en,
                    max_windows=self.max_windows,
                )
                meta["model_dir"] = str(model_dir)
            else:
                summary, lang = _extractive_summary(row_text, self.max_chars_zh, self.max_words_en, self.min_words_en)
                meta = {"providers": ["CPUExecutionProvider"], "windows": 0}
            summaries.append((key, row_text, summary, {"lang": lang, **meta}))

        if self.preserve_keys and any(key for key, _text, _summary, _meta in summaries):
            output_text = "\n".join(f"{key}\t{summary}" if key else summary for key, _text, summary, _meta in summaries)
        else:
            output_text = "\n".join(summary for _key, _text, summary, _meta in summaries)

        details = []
        for key, row_text, summary, meta in summaries:
            item: Dict[str, Any] = {
                "key": key,
                "summary": summary,
                "language": meta.get("lang"),
                "input_chars": len(row_text),
                "summary_chars": len(summary),
                "method": method,
                "runtime": {k: v for k, v in meta.items() if k != "lang"},
            }
            details.append(item)

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_text_summarize"] = {
            "method": method,
            "line_mode": self.line_mode,
            "items": details,
            "elapsed_ms": round((time.time() - start) * 1000.0, 3),
        }
        sample[self.ext_params_key] = ext
        sample[self.text_key] = output_text
        sample[self.data_key] = b""
        sample[self.filetype_key] = "txt"
        sample[self.target_type_key] = "txt"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioTextSummarize costs {time.time() - start:6f} s"
        )
        return sample
