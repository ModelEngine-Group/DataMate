# -*- coding: utf-8 -*-
"""Video subtitle OCR operator based on RapidOCR CPU.

This file replaces the previous PaddleOCR implementation.
Main goals:
  1) Avoid Paddle/PaddleX C++ inference crashes in merged environments.
  2) Keep the original subtitle pipeline: optional deborder, bottom ROI, frame sampling,
     adjacent subtitle merging, JSON + SRT outputs.
  3) Only apply conservative English cleanup rules to avoid over-correction.
"""

import os
import json
import re
import shutil
import subprocess
import tempfile
from difflib import SequenceMatcher

import cv2
import numpy as np

from datamate.core.base_op import Mapper
from .._video_common.params import parse_bool
from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.qwen_http_client import (
    qwenvl_correct_subtitle_srt,
    resolve_qwenvl_service_url,
)


# -----------------------------
# SRT / text helpers
# -----------------------------

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
            f.write(str(i) + "\n")
            f.write(f"{_fmt(float(seg['start']))} --> {_fmt(float(seg['end']))}\n")
            f.write(text + "\n\n")


def _segments_to_srt_text(segments) -> str:
    def _fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        if ms >= 1000:
            s += 1
            ms -= 1000
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, seg in enumerate(segments, 1):
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        lines.append(str(i))
        lines.append(f"{_fmt(float(seg['start']))} --> {_fmt(float(seg['end']))}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def _apply_corrected_texts(segments, corrected_items):
    if not isinstance(corrected_items, list):
        return segments, False

    corrected_by_index = {}
    for item in corrected_items:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        text = item.get("text")
        if isinstance(idx, int) and isinstance(text, str):
            corrected_by_index[idx] = _clean_text(text)

    if not corrected_by_index:
        return segments, False

    new_segments = []
    changed = False
    for i, seg in enumerate(segments, 1):
        new_seg = dict(seg)
        if i in corrected_by_index and corrected_by_index[i]:
            if corrected_by_index[i] != (seg.get("text") or ""):
                changed = True
            new_seg["text"] = corrected_by_index[i]
            new_seg["key"] = _norm_sub_key(new_seg["text"])
        new_segments.append(new_seg)
    return new_segments, changed


def _clean_text(t: str) -> str:
    if not t:
        return ""
    t = str(t).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _english_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(c.isalpha() for c in text)
    return letters / max(1, len(text))


def _fix_english_spacing_basic(text: str) -> str:
    """Light English spacing cleanup. Conservative; does not use word segmentation.

    Handles only safe cases:
      - lower + Upper: helloWorld -> hello World
      - letter + digit / digit + letter
      - punctuation followed by a letter
    """
    if not text:
        return ""
    if _english_ratio(text) < 0.40:
        return text

    t = text
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+([,.;:?!])", r"\1", t)
    t = re.sub(r"([,.;:?!])([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _fix_english_ocr_artifacts(text: str) -> str:
    """Conservative RapidOCR English subtitle artifact cleanup.

    Only fixes the high-confidence noise patterns observed in subtitles:
      - isolated single-letter subtitle: J -> removed
      - repeated leading letter before same-initial word: g gashes -> gashes
      - very common glued noise: lyou / Iyou -> you

    Avoids broad dictionary-based correction to prevent accidental deletion.
    """
    if not text:
        return ""

    t = _clean_text(text)
    if not t:
        return ""

    # Whole subtitle is a single isolated English letter: almost always noise.
    if re.fullmatch(r"[A-Za-z]", t):
        return ""

    # Remove "single letter + same-initial word" OCR echo noise.
    # Examples: "g gashes" -> "gashes", "s strength" -> "strength", "f for" -> "for".
    t = re.sub(r"\b([A-Za-z])\s+(\1[A-Za-z]{2,})\b", r"\2", t, flags=re.IGNORECASE)

    # Common single-letter glue noise observed in subtitles.
    t = re.sub(r"\b[lI]you\b", "you", t)
    t = re.sub(r"\b[lI]your\b", "your", t)

    t = re.sub(r"\s+", " ", t).strip()
    return t


def _is_noise_subtitle(text: str) -> bool:
    if not text:
        return True
    t = text.strip()
    if not t:
        return True

    # Remove punctuation/spaces before length check.
    # Requirement: if one subtitle has fewer than 3 effective characters, drop it.
    effective = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", t)
    if len(effective) < 3:
        return True

    # Symbol-only output.
    if re.fullmatch(r"[^A-Za-z0-9\u4e00-\u9fff]+", t):
        return True
    return False


def _merge_norm_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[.。,，!！?？:：;；~～_\-]+$", "", t).strip()
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


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


def _choose_better_text(a: str, b: str) -> str:
    if not a:
        return b
    if not b:
        return a
    a_score = len(_merge_nospace_text(a))
    b_score = len(_merge_nospace_text(b))
    # Very small preference for sentence-like ending punctuation.
    if re.search(r"[.。!?！？]$", a.strip()):
        a_score += 2
    if re.search(r"[.。!?！？]$", b.strip()):
        b_score += 2
    return b if b_score > a_score else a


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
        # One is contained in the other; usually OCR fluctuation of the same subtitle.
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
        if _should_merge_hit(last, hit_like, gap_merge=max(gap_merge, 1.5), sim_thr=0.86):
            last["end"] = max(float(last["end"]), float(seg["end"]))
            last["text"] = _choose_better_text(last["text"], seg["text"])
            last["key"] = _norm_sub_key(last["text"])
            last.setdefault("evidence", []).extend(seg.get("evidence", []))
        else:
            merged.append(seg)

    return merged


# -----------------------------
# Video / ROI helpers
# -----------------------------

def _roi_changed(cur_roi, last_roi, diff_thr=3.0):
    if last_roi is None:
        return True
    a = cv2.cvtColor(cur_roi, cv2.COLOR_BGR2GRAY)
    b = cv2.cvtColor(last_roi, cv2.COLOR_BGR2GRAY)
    if a.shape != b.shape:
        b = cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    diff = np.mean(np.abs(a.astype(np.float32) - b.astype(np.float32)))
    return diff >= diff_thr


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
    logger.info("crop cmd: " + " ".join(cmd2))
    p2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p2.returncode != 0:
        raise RuntimeError(f"ffmpeg crop failed.\n{p2.stderr}")
    return {"w": w, "h": h, "x": x, "y": y}


def _safe_remove(path: str):
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except Exception:
        pass


def _safe_rmtree(path: str):
    try:
        if path and os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def _prepare_roi_for_ocr(roi, upscale=1.5, sharpen=True, contrast=1.15, brightness=3):
    """Light preprocessing for subtitle ROI.

    Defaults are intentionally moderate to avoid creating duplicate-letter artifacts.
    """
    out = roi
    try:
        if upscale and float(upscale) > 1.0:
            scale = float(upscale)
            out = cv2.resize(out, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        if sharpen:
            blur = cv2.GaussianBlur(out, (0, 0), 1.0)
            out = cv2.addWeighted(out, 1.35, blur, -0.35, 0)

        if contrast != 1.0 or brightness != 0:
            out = cv2.convertScaleAbs(out, alpha=float(contrast), beta=float(brightness))
    except Exception:
        # If preprocessing fails, fall back to original ROI.
        out = roi
    return out


# -----------------------------
# RapidOCR helpers
# -----------------------------

def _build_rapid_ocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as e:
        raise RuntimeError(
            "rapidocr_onnxruntime is not installed. Please install it first: "
            "python -m uv pip install rapidocr-onnxruntime==1.4.4"
        ) from e
    return RapidOCR()


def _rapidocr_pairs(result):
    """Return [(text, score)] from RapidOCR result."""
    pairs = []
    if not result:
        return pairs
    for item in result:
        try:
            if isinstance(item, dict):
                text = item.get("text") or item.get("rec_text") or ""
                score = item.get("score") or item.get("rec_score") or 0.0
            elif isinstance(item, (list, tuple)) and len(item) >= 3:
                # Common RapidOCR format: [box, text, score]
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


class VideoSubtitleOCR(Mapper):
    """Subtitle OCR operator using RapidOCR CPU.

    Params:
      - preprocess_deborder: bool, default True
      - sample_fps: float, default 3.33  # about one frame every 0.3 sec
      - max_frames: int, default 220
      - subtitle_ratio: float, default 0.30
      - min_score: float, default 0.15
      - roi_diff_thr: float, default 3.0
      - gap_merge_sec: float, default 1.5
      - fix_english_space: bool, default True
      - ocr_upscale: float, default 1.5
      - ocr_sharpen: bool, default True
      - ocr_contrast: float, default 1.15
      - ocr_brightness: int/float, default 3
      - enable_llm_correction: bool, default False
    """

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
            if parse_bool(params.get("preprocess_deborder", True), default=True):
                deborder_mp4 = os.path.join(temp_root, "deborder.mp4")
                crop = _deborder_ffmpeg(ffmpeg_path, in_video, deborder_mp4, logger)
                with open(os.path.join(art_dir, "deborder_crop.json"), "w", encoding="utf-8") as f:
                    json.dump({"crop": crop}, f, ensure_ascii=False, indent=2)
                src_video = deborder_mp4
            else:
                src_video = in_video

            logger.info(f"video={src_video}")
            logger.info(f"out_dir={out_dir}")
            logger.info("OCR backend=RapidOCR CPU")

            ocr = _build_rapid_ocr()

            fps, w, h, total = get_video_info(src_video)
            sample_fps = float(params.get("sample_fps", 3.33))
            max_frames = int(params.get("max_frames", 220))
            subtitle_ratio = float(params.get("subtitle_ratio", 0.30))
            enable_min_score = parse_bool(params.get("enable_min_score", False), default=False)
            min_score = float(params.get("min_score", 0.15)) if enable_min_score else 0.0
            enable_roi_diff = parse_bool(params.get("enable_roi_diff_thr", False), default=False)
            roi_diff_thr = float(params.get("roi_diff_thr", 3.0)) if enable_roi_diff else 0.0
            gap_merge = float(params.get("gap_merge_sec", 1.5))
            fix_en_space = parse_bool(params.get("fix_english_space", True), default=True)

            enable_ocr_upscale = parse_bool(params.get("enable_ocr_upscale", False), default=False)
            ocr_upscale = float(params.get("ocr_upscale", 1.5)) if enable_ocr_upscale else 1.0
            ocr_sharpen = parse_bool(params.get("ocr_sharpen", True), default=True)
            enable_ocr_contrast = parse_bool(params.get("enable_ocr_contrast", False), default=False)
            ocr_contrast = float(params.get("ocr_contrast", 1.15)) if enable_ocr_contrast else 1.0
            enable_ocr_brightness = parse_bool(params.get("enable_ocr_brightness", False), default=False)
            ocr_brightness = float(params.get("ocr_brightness", 3)) if enable_ocr_brightness else 0.0
            enable_llm_correction = parse_bool(params.get("enable_llm_correction", False), default=False)
            llm_service_url = resolve_qwenvl_service_url(params.get("llm_service_url"))
            llm_language = str(params.get("llm_language", "auto") or "auto")
            llm_timeout_sec = int(params.get("llm_timeout_sec", 180))
            llm_max_new_tokens = int(params.get("llm_max_new_tokens", 1024))

            step = max(1, int(round(fps / max(sample_fps, 0.0001))))
            idxs = list(range(0, total, step))
            if max_frames and len(idxs) > max_frames:
                n = max_frames
                idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]

            logger.info(
                f"fps={fps}, total={total}, size={w}x{h}, "
                f"sample_fps={sample_fps}, frames_to_check={len(idxs)}"
            )

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

                ocr_roi = _prepare_roi_for_ocr(
                    roi,
                    upscale=ocr_upscale,
                    sharpen=ocr_sharpen,
                    contrast=ocr_contrast,
                    brightness=ocr_brightness,
                )

                jpg_path = os.path.join(frames_dir, f"subtitle_{int(fi):06d}.jpg")
                cv2.imwrite(jpg_path, ocr_roi)

                try:
                    result, elapse = ocr(jpg_path)
                except Exception as e:
                    logger.warning(f"OCR failed frame={fi}: {repr(e)}")
                    result = None
                pairs = _rapidocr_pairs(result)
                texts = [txt for (txt, sc) in pairs if txt and float(sc) >= min_score]

                text = _clean_text(" ".join(texts))
                if fix_en_space:
                    text = _fix_english_spacing_basic(text)
                    text = _fix_english_ocr_artifacts(text)

                if text and not _is_noise_subtitle(text):
                    raw_hits.append({
                        "t": t,
                        "text": text,
                        "key": _norm_sub_key(text),
                        "frame_id": int(fi),
                        "scores": [float(sc) for (_, sc) in pairs],
                    })

                _safe_remove(jpg_path)

                if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                    logger.info(f"[{k + 1}/{len(idxs)}] frame={fi} hit={1 if text else 0} len={len(text)}")

            cap.release()

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
                    last["text"] = _fix_english_ocr_artifacts(_fix_english_spacing_basic(last["text"])) if fix_en_space else last["text"]
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

            min_dur = max(0.4, 1.0 / max(sample_fps, 0.1))
            for seg in segments:
                seg["end"] = float(seg["end"] + min_dur)
                seg["text"] = _clean_text(seg.get("text", ""))

            segments = [seg for seg in segments if seg.get("text") and not _is_noise_subtitle(seg.get("text", ""))]

            llm_correction_applied = False
            corrected_srt_path = None
            llm_correction_raw_path = None
            if enable_llm_correction and segments:
                try:
                    srt_text = _segments_to_srt_text(segments)
                    llm_resp = qwenvl_correct_subtitle_srt(
                        srt_text=srt_text,
                        service_url=llm_service_url,
                        language=llm_language,
                        max_new_tokens=llm_max_new_tokens,
                        timeout=llm_timeout_sec,
                    )
                    corrected_segments, llm_correction_applied = _apply_corrected_texts(
                        segments,
                        llm_resp.get("items", []),
                    )
                    if llm_correction_applied:
                        segments = corrected_segments
                    llm_correction_raw_path = os.path.join(art_dir, "llm_subtitle_correction.json")
                    with open(llm_correction_raw_path, "w", encoding="utf-8") as f:
                        json.dump(llm_resp, f, ensure_ascii=False, indent=2)
                    logger.info(
                        f"LLM subtitle correction done. applied={llm_correction_applied}, service_url={llm_service_url}"
                    )
                except Exception as e:
                    logger.warning(f"LLM subtitle correction failed, keep OCR result. reason={repr(e)}")

            json_path = os.path.join(art_dir, "subtitles.json")
            raw_path = os.path.join(art_dir, "raw_hits.json")
            srt_path = os.path.join(art_dir, "subtitles.srt")
            if enable_llm_correction:
                corrected_srt_path = os.path.join(art_dir, "subtitles_corrected.srt")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump({"raw_hits": raw_hits}, f, ensure_ascii=False, indent=2)
            _write_srt(segments, srt_path)
            if corrected_srt_path:
                _write_srt(segments, corrected_srt_path)

            result = {
                "out_dir": out_dir,
                "subtitles_json": json_path,
                "subtitles_srt": srt_path,
                "raw_hits_json": raw_path,
                "count": len(segments),
                "llm_correction_applied": llm_correction_applied,
            }
            if corrected_srt_path:
                result["subtitles_corrected_srt"] = corrected_srt_path
            if llm_correction_raw_path:
                result["llm_correction_json"] = llm_correction_raw_path
            sample.update(result)
            logger.info(f"Done. subtitles={len(segments)} srt={srt_path}")
            return sample
        finally:
            _safe_rmtree(frames_dir)
            _safe_remove(deborder_mp4)
            _safe_rmtree(temp_root)
