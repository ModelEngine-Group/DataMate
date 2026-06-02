# -*- coding: utf-8 -*-
"""
video_text_ocr / process.py

RapidOCR CPU 版视频显著文字 OCR：
- 不依赖 PaddleOCR / PaddlePaddle。
- 使用 ffmpeg 去黑边。
- 默认扫描上方 70% 区域，用于标题、画面内显著文字、路牌、说明文字等。
- 支持 ROI 放大、锐化、对比度增强。
- 输出 text_ocr.json。
"""

import os
import json
import re
import hashlib
import shutil
import subprocess
import tempfile
from collections import Counter
from difflib import SequenceMatcher

import cv2
import numpy as np

from datamate.core.base_op import Mapper
from .._video_common.params import parse_bool
from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info


def _clean_text(t: str) -> str:
    if not t:
        return ""
    t = str(t).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _english_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(c.isalpha() and (ord(c) < 128) for c in text)
    return letters / max(1, len(text))


def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def _fix_common_contractions(text: str) -> str:
    fixes = {
        r"\bI m\b": "I'm",
        r"\bI ve\b": "I've",
        r"\bI ll\b": "I'll",
        r"\bI d\b": "I'd",
        r"\bdon t\b": "don't",
        r"\bdoesn t\b": "doesn't",
        r"\bdidn t\b": "didn't",
        r"\bcan t\b": "can't",
        r"\bisn t\b": "isn't",
        r"\bit s\b": "it's",
        r"\bthat s\b": "that's",
    }
    for pat, rep in fixes.items():
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def _fix_english_spacing(text: str, use_wordninja: bool = True) -> str:
    if not text:
        return text
    if _has_cjk(text) or _english_ratio(text) < 0.40:
        return _clean_text(text)

    t = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+([,.;:?!])", r"\1", t)
    t = re.sub(r"([,.;:?!])([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()

    if use_wordninja:
        try:
            import wordninja

            def split_long_word(m):
                s = m.group(0)
                if len(s) < 9 or (s.isupper() and len(s) <= 12):
                    return s
                parts = wordninja.split(s)
                return " ".join(parts) if len(parts) > 1 else s

            t = re.sub(r"[A-Za-z]{9,}", split_long_word, t)
            t = _fix_common_contractions(t)
            t = re.sub(r"\s+", " ", t).strip()
        except Exception:
            pass

    return t


def _norm_text(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff\s]", " ", t)
    t = re.sub(r"\s+", "", t)
    return t


def _text_sim(a: str, b: str) -> float:
    a1 = _norm_text(a)
    b1 = _norm_text(b)
    if not a1 or not b1:
        return 0.0
    if a1 == b1:
        return 1.0
    return SequenceMatcher(None, a1, b1).ratio()


def _is_garbage_text(t: str) -> bool:
    if not t:
        return True

    s = t.replace(" ", "")
    if len(s) < 2:
        return True

    valid = re.findall(r"[0-9A-Za-z\u4e00-\u9fff]", s)
    if len(valid) < 2:
        return True

    cnt = Counter(s.lower())
    most = cnt.most_common(1)[0][1]
    if most / max(1, len(s)) > 0.65:
        return True

    letters = sum(c.isalpha() for c in s)
    if letters / max(1, len(s)) > 0.9:
        uniq = len(set(s.lower()))
        if uniq <= 4 and len(s) >= 6:
            return True

    return False


def _roi_changed(cur_roi, last_roi, diff_thr=6.0):
    if last_roi is None:
        return True
    if diff_thr <= 0:
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
        "-f", "null", "-"
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
        out_video
    ]
    logger.info("crop cmd: " + " ".join(cmd2))
    p2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p2.returncode != 0:
        raise RuntimeError(f"ffmpeg crop failed.\n{p2.stderr}")
    return {"w": w, "h": h, "x": x, "y": y}


def _enhance_roi(roi, upscale=1.5, sharpen=True, contrast=1.20, brightness=4):
    out = roi
    if upscale and float(upscale) > 1.0:
        out = cv2.resize(out, None, fx=float(upscale), fy=float(upscale), interpolation=cv2.INTER_CUBIC)

    if sharpen:
        blur = cv2.GaussianBlur(out, (0, 0), 1.0)
        out = cv2.addWeighted(out, 1.5, blur, -0.5, 0)

    if contrast and (abs(float(contrast) - 1.0) > 1e-6 or int(brightness) != 0):
        out = cv2.convertScaleAbs(out, alpha=float(contrast), beta=int(brightness))

    return out


def _rapidocr_extract(result, min_score=0.0):
    out = []
    if not result:
        return out

    for item in result:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                txt = str(item[1])
                score = float(item[2])
                if txt and score >= min_score:
                    out.append((txt, score))
            elif isinstance(item, dict):
                txt = item.get("text") or item.get("rec_text") or ""
                score = float(item.get("score", item.get("rec_score", 0.0)))
                if txt and score >= min_score:
                    out.append((str(txt), score))
        except Exception:
            continue
    return out


def _build_rapid_ocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except Exception as e:
        raise RuntimeError(
            "rapidocr_onnxruntime is not installed. Please rebuild the runtime image with runtime/ops dependencies."
        ) from e
    return RapidOCR()


def _dedup_hits(hits, sim_thr=0.92, time_window=2.0):
    out = []
    for hit in hits:
        if not out:
            out.append(hit)
            continue

        last = out[-1]
        if hit["t"] - last["t"] <= time_window and _text_sim(hit["text"], last["text"]) >= sim_thr:
            if len(_norm_text(hit["text"])) > len(_norm_text(last["text"])):
                out[-1] = hit
        else:
            out.append(hit)
    return out


def _frame_digest(image) -> str:
    if image is None:
        return ""
    return hashlib.sha1(image.tobytes()).hexdigest()


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


class VideoTextOCR(Mapper):
    """显著文字 OCR：RapidOCR CPU 版。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample, params=None):
        params = params or self.params
        in_video = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")
        op_name = "video_text_ocr"

        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        logger = get_logger(op_name, log_dir)
        temp_root = ensure_dir(os.path.join(art_dir, "_tmp_runtime"))
        frames_dir = tempfile.mkdtemp(prefix="frames_", dir=temp_root)
        deborder_mp4 = None

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found")
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
            logger.info("OCR backend=rapidocr_onnxruntime CPU")

            ocr = _build_rapid_ocr()

            fps, w, h, total = get_video_info(src_video)
            sample_fps = float(params.get("sample_fps", 1.0))
            max_frames = int(params.get("max_frames", 160))
            top_ratio = float(params.get("top_ratio", 0.70))
            enable_min_score = parse_bool(params.get("enable_min_score", False), default=False)
            min_score = float(params.get("min_score", 0.20)) if enable_min_score else 0.0
            enable_roi_diff = parse_bool(params.get("enable_roi_diff_thr", False), default=False)
            roi_diff_thr = float(params.get("roi_diff_thr", 6.0)) if enable_roi_diff else 0.0
            fix_en_space = parse_bool(params.get("fix_english_space", True), default=True)
            use_wordninja = parse_bool(params.get("use_wordninja", True), default=True)

            enable_ocr_upscale = parse_bool(params.get("enable_ocr_upscale", False), default=False)
            ocr_upscale = float(params.get("ocr_upscale", 1.5)) if enable_ocr_upscale else 1.0
            ocr_sharpen = parse_bool(params.get("ocr_sharpen", True), default=True)
            enable_ocr_contrast = parse_bool(params.get("enable_ocr_contrast", False), default=False)
            ocr_contrast = float(params.get("ocr_contrast", 1.20)) if enable_ocr_contrast else 1.0
            enable_ocr_brightness = parse_bool(params.get("enable_ocr_brightness", False), default=False)
            ocr_brightness = int(params.get("ocr_brightness", 4)) if enable_ocr_brightness else 0

            start_sec = float(params.get("start_sec", 0.0))
            end_sec = params.get("end_sec", None)
            end_sec = float(end_sec) if end_sec not in (None, "") else None

            step = max(1, int(round(fps / max(sample_fps, 0.0001))))
            start_frame = max(0, int(start_sec * fps))
            end_frame = total if end_sec is None else min(total, int(end_sec * fps))
            idxs = list(range(start_frame, end_frame, step))

            if max_frames and len(idxs) > max_frames:
                n = max_frames
                idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]

            cap = cv2.VideoCapture(src_video)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {src_video}")

            hits = []
            last_roi = None
            last_roi_digest = None
            exact_frame_dedup = parse_bool(params.get("exact_frame_dedup", True), default=True)

            for k, fi in enumerate(idxs):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue

                t = float(fi / fps) if fps else 0.0
                y1 = int(h * top_ratio)
                roi_raw = frame[0:y1, 0:w]

                if not _roi_changed(roi_raw, last_roi, diff_thr=roi_diff_thr):
                    continue
                last_roi = roi_raw.copy()

                roi = _enhance_roi(
                    roi_raw,
                    upscale=ocr_upscale,
                    sharpen=ocr_sharpen,
                    contrast=ocr_contrast,
                    brightness=ocr_brightness,
                )

                roi_digest = _frame_digest(roi) if exact_frame_dedup else None
                if exact_frame_dedup and roi_digest and roi_digest == last_roi_digest:
                    logger.info(f"Skip exact duplicate ROI frame={fi}")
                    continue
                last_roi_digest = roi_digest

                jpg_path = os.path.join(frames_dir, f"text_{int(fi):06d}.jpg")
                cv2.imwrite(jpg_path, roi)

                try:
                    result, elapse = ocr(jpg_path)
                except Exception as e:
                    logger.warning(f"OCR failed frame={fi}: {repr(e)}")
                    result = None

                pairs = _rapidocr_extract(result, min_score=min_score)
                texts = [txt for (txt, sc) in pairs]
                text = _clean_text(" ".join(texts))

                if fix_en_space:
                    text = _fix_english_spacing(text, use_wordninja=use_wordninja)

                if text and (not _is_garbage_text(text)):
                    hits.append({
                        "t": t,
                        "frame_id": int(fi),
                        "text": text,
                        "score": max([sc for _, sc in pairs], default=0.0),
                    })

                _safe_remove(jpg_path)

                if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                    logger.info(f"[{k+1}/{len(idxs)}] frame={fi} hit={1 if text else 0} len={len(text)} text={text[:60]!r}")

            cap.release()

            hits = _dedup_hits(
                hits,
                sim_thr=float(params.get("dedup_sim_thr", 0.92)),
                time_window=float(params.get("dedup_time_window", 2.0)),
            )

            json_path = os.path.join(art_dir, "text_ocr.json")
            raw_path = os.path.join(art_dir, "raw_text_hits.json")

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump({"hits": hits}, f, ensure_ascii=False, indent=2)

            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump({"hits": hits}, f, ensure_ascii=False, indent=2)

            result = {
                "out_dir": out_dir,
                "text_ocr_json": json_path,
                "raw_text_hits_json": raw_path,
                "count": len(hits),
            }
            sample.update(result)
            logger.info(f"Done. hits={len(hits)}")
            return sample
        finally:
            _safe_rmtree(frames_dir)
            _safe_remove(deborder_mp4)
            _safe_rmtree(temp_root)
