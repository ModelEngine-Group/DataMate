# -*- coding: utf-8 -*-
import os
import json
import re
import shutil
import subprocess
import cv2
import numpy as np
import inspect
from collections import Counter

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from paddleocr import PaddleOCR
from .._video_common.model_paths import resolve_model_path

def build_paddle_ocr(params, ocr_lang: str, use_angle_cls: bool):
    """
    默认模型目录：
      /mnt/models/ocr/det
      /mnt/models/ocr/rec
      /mnt/models/ocr/cls
    也支持 params['ocr_model_dir'] 指定（相对/绝对）。
    """
    ocr_root = resolve_model_path(params, "ocr_model_dir", "ocr")
    det_dir = os.path.join(ocr_root, "det")
    rec_dir = os.path.join(ocr_root, "rec")
    cls_dir = os.path.join(ocr_root, "cls")

    # 目录不存在就直接报错，让用户去模型仓下载到固定位置
    for p in [det_dir, rec_dir] + ([cls_dir] if use_angle_cls else []):
        if not os.path.exists(p):
            raise RuntimeError(f"PaddleOCR model dir not found: {p}. Please download OCR models into model repo path.")

    sig = inspect.signature(PaddleOCR.__init__)
    kw = {"lang": ocr_lang}
    if "use_angle_cls" in sig.parameters:
        kw["use_angle_cls"] = use_angle_cls
    # PaddleOCR 3.4.0 支持这些
    if "det_model_dir" in sig.parameters:
        kw["det_model_dir"] = det_dir
    if "rec_model_dir" in sig.parameters:
        kw["rec_model_dir"] = rec_dir
    if "cls_model_dir" in sig.parameters and use_angle_cls:
        kw["cls_model_dir"] = cls_dir

    return PaddleOCR(**kw)

def _clean_text(t: str) -> str:
    if not t:
        return ""
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _roi_changed(cur_roi, last_roi, diff_thr=6.0):
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


def _extract_texts_from_any(res):
    out = []
    if isinstance(res, dict):
        for kt in ["rec_texts", "texts", "text"]:
            if kt in res:
                texts = res[kt]
                scores = res.get("rec_scores", res.get("scores", res.get("score", None)))
                if isinstance(texts, str):
                    out.append((texts, float(scores) if scores is not None else 0.0))
                    return out
                if isinstance(texts, (list, tuple)):
                    if isinstance(scores, (list, tuple)) and len(scores) == len(texts):
                        for t, s in zip(texts, scores):
                            out.append((str(t), float(s)))
                    else:
                        for t in texts:
                            out.append((str(t), float(scores) if scores is not None else 0.0))
                    return out
        if "result" in res:
            return _extract_texts_from_any(res["result"])

    if isinstance(res, list):
        if len(res) == 0:
            return out
        if isinstance(res[0], dict):
            for item in res:
                out.extend(_extract_texts_from_any(item))
            return out
        lines = res[0] if isinstance(res[0], list) else res
        for line in lines:
            try:
                if isinstance(line, (list, tuple)) and len(line) >= 2:
                    info = line[1]
                    if isinstance(info, (list, tuple)) and len(info) >= 2:
                        out.append((str(info[0]), float(info[1])))
                    elif isinstance(info, str):
                        out.append((info, 0.0))
            except Exception:
                continue
        return out

    try:
        s = str(res)
        if s:
            out.append((s, 0.0))
    except Exception:
        pass
    return out


def _is_garbage_text(t: str) -> bool:
    if not t:
        return True
    s = t.replace(" ", "")
    if len(s) < 2:
        return True
    letters = sum(c.isalpha() for c in s)
    if letters / len(s) > 0.9:
        uniq = len(set(s.lower()))
        if uniq <= 5:
            return True
    cnt = Counter(s.lower())
    most = cnt.most_common(1)[0][1]
    if most / len(s) > 0.65:
        return True
    return False


class VideoTextOCR:
    """显著文字 OCR（自动去黑边 + 上70%）

    params:
      - preprocess_deborder: bool, default True
      - sample_fps: float, default 0.5
      - max_frames: int, default 120
      - top_ratio: float, default 0.70
      - ocr_lang: ch|en, default ch
      - min_score: float, default 0.0
      - roi_diff_thr: float, default 6.0
    """

    @staticmethod
    def execute(sample, params):
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

        in_video = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")
        op_name = "video_text_ocr"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger(op_name, log_dir)

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found")

        if params.get("preprocess_deborder", True):
            deborder_mp4 = os.path.join(art_dir, "deborder.mp4")
            crop = _deborder_ffmpeg(ffmpeg_path, in_video, deborder_mp4, logger)
            with open(os.path.join(art_dir, "deborder_crop.json"), "w", encoding="utf-8") as f:
                json.dump({"crop": crop, "deborder_mp4": deborder_mp4}, f, ensure_ascii=False, indent=2)
            src_video = deborder_mp4
        else:
            src_video = in_video

        logger.info(f"video={src_video}")
        logger.info(f"out_dir={out_dir}")

        from paddleocr import PaddleOCR
        ocr_lang = params.get("ocr_lang", "ch")
        ocr = build_paddle_ocr(params, ocr_lang=ocr_lang, use_angle_cls=False)   

        fps, w, h, total = get_video_info(src_video)
        sample_fps = float(params.get("sample_fps", 0.5))
        max_frames = int(params.get("max_frames", 120))
        top_ratio = float(params.get("top_ratio", 0.70))
        min_score = float(params.get("min_score", 0.0))
        roi_diff_thr = float(params.get("roi_diff_thr", 6.0))

        step = max(1, int(round(fps / max(sample_fps, 0.0001))))
        idxs = list(range(0, total, step))
        if max_frames and len(idxs) > max_frames:
            n = max_frames
            idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]

        cap = cv2.VideoCapture(src_video)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {src_video}")

        hits = []
        last_roi = None

        for k, fi in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            t = float(fi / fps) if fps else 0.0
            y1 = int(h * top_ratio)
            roi = frame[0:y1, 0:w]

            if not _roi_changed(roi, last_roi, diff_thr=roi_diff_thr):
                continue
            last_roi = roi

            jpg_path = os.path.join(frames_dir, f"text_{int(fi):06d}.jpg")
            cv2.imwrite(jpg_path, roi)

            res = ocr.ocr(roi)
            pairs = _extract_texts_from_any(res)
            texts = [txt for (txt, sc) in pairs if txt and float(sc) >= min_score]
            text = _clean_text(" ".join(texts))

            if text and (not _is_garbage_text(text)):
                hits.append({"t": t, "frame_id": int(fi), "text": text, "jpg": jpg_path})

            if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                logger.info(f"[{k+1}/{len(idxs)}] frame={fi} hit={1 if text else 0} len={len(text)}")

        cap.release()

        json_path = os.path.join(art_dir, "text_ocr.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"hits": hits}, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. hits={len(hits)}")
        return {"out_dir": out_dir, "text_ocr_json": json_path, "count": len(hits)}