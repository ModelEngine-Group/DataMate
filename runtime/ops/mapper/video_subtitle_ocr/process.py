# -*- coding: utf-8 -*-
"""Video subtitle OCR with optional LLM backend and optional postprocessing."""

import json
import os
import re
import shutil
import subprocess
import tempfile
from difflib import SequenceMatcher

import cv2
import numpy as np

from datamate.core.base_op import Mapper
from .._video_common.io_video import get_video_info
from .._video_common.log import get_logger
from .._video_common.params import parse_bool
from .._video_common.paths import ensure_dir, make_run_dir
from .._video_common.qwen_http_client import (
    qwenvl_read_subtitle_by_image_path,
    resolve_qwenvl_service_url,
)


def _write_srt(segments, srt_path):
    def _fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        if ms >= 1000:
            s += 1
            ms -= 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            f.write(f"{i}\n")
            f.write(f"{_fmt(float(seg['start']))} --> {_fmt(float(seg['end']))}\n")
            f.write(text + "\n\n")


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).strip().replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text)


def _english_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(c.isalpha() for c in text)
    return letters / max(1, len(text))


def _fix_english_spacing_basic(text: str) -> str:
    if not text or _english_ratio(text) < 0.40:
        return text
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([A-Za-z])", r"\1 \2", text)
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"([,.;:?!])([A-Za-z])", r"\1 \2", text)
    return re.sub(r"\s+", " ", text).strip()


def _fix_english_ocr_artifacts(text: str) -> str:
    if not text:
        return ""
    text = _clean_text(text)
    if not text:
        return ""
    if re.fullmatch(r"[A-Za-z]", text):
        return ""
    text = re.sub(r"\b([A-Za-z])\s+(\1[A-Za-z]{2,})\b", r"\2", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[lI]you\b", "you", text)
    text = re.sub(r"\b[lI]your\b", "your", text)
    text = re.sub(r"\byouf(?:re|r)\b", "you're", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def _is_noise_subtitle(text: str) -> bool:
    if not text:
        return True
    text = text.strip()
    if not text:
        return True

    effective = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", text)
    if len(effective) < 2:
        return True

    if re.fullmatch(r"[^A-Za-z0-9\u4e00-\u9fff]+", text):
        return True

    explanation_patterns = [
        r"\bi'?m sorry\b",
        r"\bthere is no subtitle\b",
        r"\bno subtitle present\b",
        r"\bno readable subtitle\b",
        r"\bthe image you provided\b",
        r"\bno text\b",
    ]
    for pattern in explanation_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True

    if re.search(r"\b(?:poog|poag|youcans)\b", text, flags=re.IGNORECASE):
        return True
    return False


def _merge_norm_text(text: str) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _merge_nospace_text(text: str) -> str:
    return re.sub(r"\s+", "", _merge_norm_text(text))


def _norm_sub_key(text: str) -> str:
    return _merge_nospace_text(text)


def _text_sim(a: str, b: str) -> float:
    a1 = _merge_nospace_text(a)
    b1 = _merge_nospace_text(b)
    if not a1 or not b1:
        return 0.0
    if a1 == b1:
        return 1.0
    return SequenceMatcher(None, a1, b1).ratio()


def _subtitle_quality_score(text: str) -> float:
    text = _clean_text(text)
    if not text:
        return -999.0

    effective = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", text)
    score = float(len(effective))

    if re.search(r"[.。!?？！'\"]$", text):
        score += 1.5

    if re.search(r"\b(?:poog|poag|youcans)\b", text, flags=re.IGNORECASE):
        score -= 6.0

    for pattern in (
        r"\bi'?m sorry\b",
        r"\bthere is no subtitle\b",
        r"\bno subtitle present\b",
        r"\bno readable subtitle\b",
        r"\bthe image you provided\b",
        r"\bno text\b",
    ):
        if re.search(pattern, text, flags=re.IGNORECASE):
            score -= 10.0
    return score


def _choose_better_text(a: str, b: str) -> str:
    if not a:
        return b
    if not b:
        return a
    return b if _subtitle_quality_score(b) > _subtitle_quality_score(a) else a


def _should_merge_hit(last_seg, hit, gap_merge: float, sim_thr: float = 0.88) -> bool:
    dt = float(hit["t"]) - float(last_seg["end"])
    if dt > gap_merge:
        return False

    if hit.get("key") and hit.get("key") == last_seg.get("key"):
        return True

    a = _merge_nospace_text(last_seg.get("text", ""))
    b = _merge_nospace_text(hit.get("text", ""))
    if a and b:
        if a == b:
            return True
        if (a in b or b in a) and dt <= max(1.5, gap_merge):
            return True
    return _text_sim(last_seg.get("text", ""), hit.get("text", "")) >= sim_thr


def _post_merge_segments(segments, gap_merge: float):
    if not segments:
        return segments

    merged = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        hit_like = {"t": seg["start"], "text": seg["text"], "key": seg.get("key", "")}
        if _should_merge_hit(last, hit_like, gap_merge=max(gap_merge, 1.5), sim_thr=0.84):
            last["end"] = max(float(last["end"]), float(seg["end"]))
            last["text"] = _choose_better_text(last["text"], seg["text"])
            last["key"] = _norm_sub_key(last["text"])
            last.setdefault("evidence", []).extend(seg.get("evidence", []))
        else:
            merged.append(seg)
    return merged


def _roi_changed(cur_roi, last_roi, diff_thr=3.0):
    if last_roi is None or diff_thr <= 0:
        return True
    a = cv2.cvtColor(cur_roi, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(last_roi, cv2.COLOR_BGR2GRAY)
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    diff = np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32)))
    return diff >= diff_thr


def _prepare_roi_image(roi, upscale=1.0, sharpen=False, contrast=1.0, brightness=0.0):
    out = roi
    if upscale and abs(float(upscale) - 1.0) > 1e-6:
        h, w = out.shape[:2]
        out = cv2.resize(out, (int(w * upscale), int(h * upscale)), interpolation=cv2.INTER_CUBIC)
    if contrast and abs(float(contrast) - 1.0) > 1e-6:
        out = cv2.convertScaleAbs(out, alpha=float(contrast), beta=0)
    if brightness and abs(float(brightness)) > 1e-6:
        out = cv2.convertScaleAbs(out, alpha=1.0, beta=float(brightness))
    if sharpen:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
        out = cv2.filter2D(out, -1, kernel)
    return out


def _even(x: int) -> int:
    return x - (x % 2)


def _parse_cropdetect(stderr: str):
    m_last = None
    for line in stderr.splitlines():
        m = re.search(r"crop=(\d+):(\d+):(\d+):(\d+)", line)
        if m:
            m_last = m
    if not m_last:
        return None
    w, h, x, y = map(int, m_last.groups())
    return (_even(w), _even(h), _even(x), _even(y))


def _deborder_ffmpeg(ffmpeg_path: str, in_video: str, out_video: str, logger):
    cmd1 = [
        ffmpeg_path, "-hide_banner", "-y",
        "-ss", "0", "-i", in_video, "-t", "2",
        "-vf", "cropdetect=24:16:0",
        "-f", "null", "-",
    ]
    logger.info("cropdetect cmd: " + " ".join(cmd1))
    p1 = subprocess.run(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    crop = _parse_cropdetect(p1.stderr)
    if not crop:
        logger.warning("cropdetect found nothing, keep original (copy).")
        cmdc = [ffmpeg_path, "-hide_banner", "-y", "-i", in_video, "-c", "copy", out_video]
        p = subprocess.run(cmdc, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"ffmpeg copy failed.\n{p.stderr}")
        return None

    w, h, x, y = crop
    cmd2 = [
        ffmpeg_path, "-hide_banner", "-y",
        "-i", in_video,
        "-vf", f"crop={w}:{h}:{x}:{y}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        out_video,
    ]
    logger.info("crop apply cmd: " + " ".join(cmd2))
    p2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p2.returncode != 0:
        raise RuntimeError(f"ffmpeg crop failed.\n{p2.stderr}")
    return {"w": w, "h": h, "x": x, "y": y}


def _build_rapidocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as e:
        raise RuntimeError(
            "rapidocr_onnxruntime is not installed. Please install it to use subtitle OCR without the LLM."
        ) from e
    return RapidOCR()


def _rapidocr_pairs(result):
    pairs = []
    if not result:
        return pairs
    for item in result:
        try:
            if isinstance(item, dict):
                text = item.get("text") or item.get("rec_text") or ""
                score = item.get("score") or item.get("rec_score") or 0.0
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                text = item[1]
                score = item[2]
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                text = item[1]
                score = 0.0
            else:
                continue
            text = _clean_text(str(text))
            if text:
                pairs.append((text, float(score)))
        except Exception:
            continue
    return pairs


def _safe_remove(path: str | None):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def _safe_rmtree(path: str | None):
    if path and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)


class VideoSubtitleOCR(Mapper):
    """Subtitle OCR with selectable recognition backend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample, params=None):
        params = params or self.params
        in_video = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")
        op_name = "video_subtitle_ocr"

        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        logger = get_logger(op_name, log_dir)
        temp_root = ensure_dir(os.path.join(art_dir, "_tmp_runtime"))
        frames_dir = tempfile.mkdtemp(prefix="frames_", dir=temp_root)
        deborder_mp4 = None

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg or pass ffmpeg_path.")

        try:
            if parse_bool(params.get("preprocess_deborder", False), default=False):
                deborder_mp4 = os.path.join(temp_root, "deborder.mp4")
                crop = _deborder_ffmpeg(ffmpeg_path, in_video, deborder_mp4, logger)
                with open(os.path.join(art_dir, "deborder_crop.json"), "w", encoding="utf-8") as f:
                    json.dump({"crop": crop}, f, ensure_ascii=False, indent=2)
                src_video = deborder_mp4
            else:
                src_video = in_video

            fps, w, h, total = get_video_info(src_video)
            sample_fps = float(params.get("sample_fps", 2.0))
            max_frames = int(params.get("max_frames", 220))
            subtitle_ratio = float(params.get("subtitle_ratio", 0.30))
            enable_roi_diff = parse_bool(params.get("enable_roi_diff_thr", False), default=False)
            roi_diff_thr = float(params.get("roi_diff_thr", 3.0)) if enable_roi_diff else 0.0

            enable_ocr_upscale = parse_bool(params.get("enable_ocr_upscale", False), default=False)
            ocr_upscale = float(params.get("ocr_upscale", 1.5)) if enable_ocr_upscale else 1.0
            ocr_sharpen = parse_bool(params.get("ocr_sharpen", False), default=False)
            enable_ocr_contrast = parse_bool(params.get("enable_ocr_contrast", False), default=False)
            ocr_contrast = float(params.get("ocr_contrast", 1.15)) if enable_ocr_contrast else 1.0
            enable_ocr_brightness = parse_bool(params.get("enable_ocr_brightness", False), default=False)
            ocr_brightness = float(params.get("ocr_brightness", 3)) if enable_ocr_brightness else 0.0

            enable_llm = parse_bool(params.get("enable_llm", False), default=False)
            llm_service_url = resolve_qwenvl_service_url(params.get("llm_service_url"))
            llm_language = str(params.get("llm_language", "auto") or "auto")
            llm_timeout_sec = int(params.get("llm_timeout_sec", 180))
            llm_max_new_tokens = int(params.get("llm_max_new_tokens", 96))

            enable_postprocess = parse_bool(params.get("enable_postprocess", True), default=True)
            min_score = float(params.get("min_score", 0.15))
            gap_merge = float(params.get("gap_merge_sec", 1.5))

            step = max(1, int(round(fps / max(sample_fps, 0.0001))))
            idxs = list(range(0, total, step))
            if max_frames and len(idxs) > max_frames:
                n = max_frames
                idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]

            logger.info(f"video={src_video}")
            logger.info(f"out_dir={out_dir}")
            logger.info(f"subtitle_backend={'qwen_vl' if enable_llm else 'rapidocr'}")
            logger.info(
                f"fps={fps}, total={total}, size={w}x{h}, "
                f"sample_fps={sample_fps}, frames_to_check={len(idxs)}"
            )

            ocr = None if enable_llm else _build_rapidocr()

            cap = cv2.VideoCapture(src_video)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {src_video}")

            raw_hits = []
            last_roi = None

            for k, fi in enumerate(idxs):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue

                t = float(fi / fps) if fps else 0.0
                y0 = int(h * (1.0 - subtitle_ratio))
                roi = frame[y0:h, 0:w]

                if not _roi_changed(roi, last_roi, diff_thr=roi_diff_thr):
                    continue
                last_roi = roi

                roi_img = _prepare_roi_image(
                    roi,
                    upscale=ocr_upscale,
                    sharpen=ocr_sharpen,
                    contrast=ocr_contrast,
                    brightness=ocr_brightness,
                )
                jpg_path = os.path.join(frames_dir, f"subtitle_{int(fi):06d}.jpg")
                cv2.imwrite(jpg_path, roi_img)

                backend_meta = {}
                text = ""
                try:
                    if enable_llm:
                        llm_resp = qwenvl_read_subtitle_by_image_path(
                            image_path=jpg_path,
                            service_url=llm_service_url,
                            max_new_tokens=llm_max_new_tokens,
                            language=llm_language,
                            timeout=llm_timeout_sec,
                        )
                        backend_meta = {"llm": llm_resp}
                        text = _clean_text(llm_resp.get("text", ""))
                    else:
                        result, _ = ocr(jpg_path)
                        pairs = _rapidocr_pairs(result)
                        texts = [txt for (txt, score) in pairs if txt and float(score) >= min_score]
                        backend_meta = {
                            "ocr_pairs": [{"text": txt, "score": float(score)} for (txt, score) in pairs]
                        }
                        text = _clean_text(" ".join(texts))
                except Exception as e:
                    logger.warning(f"subtitle read failed frame={fi}: {repr(e)}")
                    backend_meta = {"error": repr(e)}
                    text = ""
                finally:
                    _safe_remove(jpg_path)

                if enable_postprocess and text:
                    text = _fix_english_spacing_basic(text)
                    text = _fix_english_ocr_artifacts(text)

                if not text:
                    continue
                if enable_postprocess and _is_noise_subtitle(text):
                    continue

                raw_hits.append({
                    "t": t,
                    "text": text,
                    "key": _norm_sub_key(text) if enable_postprocess else text,
                    "frame_id": int(fi),
                    "backend": "qwen_vl" if enable_llm else "rapidocr",
                    **backend_meta,
                })

                if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                    logger.info(
                        f"[{k + 1}/{len(idxs)}] frame={fi} backend={'llm' if enable_llm else 'ocr'} "
                        f"hit={1 if text else 0} len={len(text)}"
                    )

            cap.release()

            min_dur = max(0.4, 1.0 / max(sample_fps, 0.1))

            if enable_postprocess:
                segments = []
                for hit in raw_hits:
                    if not segments:
                        segments.append({
                            "start": hit["t"],
                            "end": hit["t"],
                            "text": hit["text"],
                            "key": hit["key"],
                            "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"]}],
                        })
                        continue

                    last = segments[-1]
                    if _should_merge_hit(last, hit, gap_merge=gap_merge, sim_thr=0.88):
                        last["end"] = hit["t"]
                        last["text"] = _choose_better_text(last["text"], hit["text"])
                        last["text"] = _fix_english_ocr_artifacts(_fix_english_spacing_basic(last["text"]))
                        last["key"] = _norm_sub_key(last["text"])
                        last["evidence"].append({"t": hit["t"], "frame_id": hit["frame_id"]})
                    else:
                        segments.append({
                            "start": hit["t"],
                            "end": hit["t"],
                            "text": hit["text"],
                            "key": hit["key"],
                            "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"]}],
                        })

                segments = _post_merge_segments(segments, gap_merge=gap_merge)
                for seg in segments:
                    seg["end"] = float(seg["end"] + min_dur)
                    seg["text"] = _clean_text(seg.get("text", ""))
                segments = [
                    seg for seg in segments
                    if seg.get("text") and not _is_noise_subtitle(seg.get("text", ""))
                ]
            else:
                segments = []
                for hit in raw_hits:
                    segments.append({
                        "start": hit["t"],
                        "end": float(hit["t"] + min_dur),
                        "text": _clean_text(hit["text"]),
                        "key": hit.get("key", hit["text"]),
                        "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"]}],
                    })

            json_path = os.path.join(art_dir, "subtitles.json")
            raw_path = os.path.join(art_dir, "raw_hits.json")
            srt_path = os.path.join(art_dir, "subtitles.srt")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump({"raw_hits": raw_hits}, f, ensure_ascii=False, indent=2)
            _write_srt(segments, srt_path)

            result = {
                "out_dir": out_dir,
                "subtitles_json": json_path,
                "subtitles_srt": srt_path,
                "raw_hits_json": raw_path,
                "count": len(segments),
                "subtitle_backend": "qwen_vl" if enable_llm else "rapidocr",
                "postprocess_enabled": bool(enable_postprocess),
            }
            sample.update(result)
            logger.info(f"Done. subtitles={len(segments)} srt={srt_path}")
            return sample
        finally:
            _safe_rmtree(frames_dir)
            _safe_remove(deborder_mp4)
            _safe_rmtree(temp_root)
