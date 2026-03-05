# -*- coding: utf-8 -*-
import os
import json
import re
import shutil
import subprocess
import cv2
import numpy as np

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info


def _write_srt(segments, srt_path):
    def _fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(str(i) + "\n")
            f.write(f"{_fmt(seg['start'])} --> {_fmt(seg['end'])}\n")
            f.write((seg.get("text") or "").strip() + "\n\n")


def _clean_text(t: str) -> str:
    if not t:
        return ""
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _english_ratio(text: str) -> float:
    if not text:
        return 0.0
    letters = sum(c.isalpha() for c in text)
    return letters / max(1, len(text))


def _fix_english_spacing(text: str) -> str:
    """英文字幕空格修复（轻量规则，避免影响中文）"""
    if not text:
        return text
    if _english_ratio(text) < 0.40:
        return text

    t = text

    # 小写后接大写：ThisIs -> This Is
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)

    # 字母数字边界：A1 / 1A
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)

    # 标点前去空格，标点后若紧跟字母则补空格（保守）
    t = re.sub(r"\s+([,.;:?!])", r"\1", t)
    t = re.sub(r"([,.;:?!])([A-Za-z])", r"\1 \2", t)

    # 多空格压缩
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _norm_sub_key(text: str) -> str:
    """用于合并的规范化 key：空格归一、末尾标点归一、英文小写化"""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    # 去掉末尾重复标点（中英文都考虑）
    t = re.sub(r"[.。!?！？]+$", "", t).strip()

    # 英文占比高则统一小写，便于合并
    if _english_ratio(t) > 0.40:
        t = t.lower()

    return t


def _roi_changed(cur_roi, last_roi, diff_thr=4.0):
    """diff_thr 调低一点更敏感，避免跳过字幕变化"""
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
    """
    兼容 PaddleOCR 多种返回：
    - 传统：res = [ [ [box,(text,score)], ... ] ]
    - 新 pipeline/dict：res 可能是 dict/对象，里头有 'rec_texts'/'rec_scores' 或 'texts'/'scores'
    返回: list[(text,score)]
    """
    out = []

    # dict 风格
    if isinstance(res, dict):
        keys_text = ["rec_texts", "texts", "text"]
        keys_score = ["rec_scores", "scores", "score"]
        texts = None
        scores = None
        for kt in keys_text:
            if kt in res:
                texts = res[kt]
                break
        for ks in keys_score:
            if ks in res:
                scores = res[ks]
                break

        if texts is not None:
            if isinstance(texts, str):
                out.append((texts, float(scores) if scores is not None else 0.0))
                return out
            if isinstance(texts, (list, tuple)):
                if scores is None:
                    for t in texts:
                        out.append((str(t), 0.0))
                else:
                    if isinstance(scores, (list, tuple)) and len(scores) == len(texts):
                        for t, s in zip(texts, scores):
                            out.append((str(t), float(s)))
                    else:
                        for t in texts:
                            out.append((str(t), float(scores) if scores is not None else 0.0))
                return out

        if "result" in res:
            return _extract_texts_from_any(res["result"])

    # list 风格（传统）
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

    # 兜底
    try:
        s = str(res)
        if s:
            out.append((s, 0.0))
    except Exception:
        pass
    return out


class VideoSubtitleOCR:
    """字幕 OCR（自动去黑边 + 固定下30% + 英文空格修复 + 去重合并）

    params:
      - preprocess_deborder: bool, default True
      - sample_fps: float, default 1.0
      - max_frames: int, default 240
      - subtitle_ratio: float, default 0.30
      - ocr_lang: ch|en, default ch
      - min_score: float, default 0.0
      - roi_diff_thr: float, default 4.0
      - gap_merge_sec: float, default 1.2     # ✅ 更容易合并跨帧字幕
      - fix_english_space: bool, default True # ✅ 英文空格修复开关

    outputs:
      - artifacts/subtitles.json
      - artifacts/subtitles.srt
      - artifacts/frames/subtitle_*.jpg
      - artifacts/deborder.mp4 (if preprocess_deborder=True)
    """

    @staticmethod
    def execute(sample, params):
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

        in_video = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")
        op_name = "video_subtitle_ocr"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger(op_name, log_dir)

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found")

        # ✅ 默认自动去黑边
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
        ocr = PaddleOCR(use_angle_cls=True, lang=ocr_lang)

        fps, w, h, total = get_video_info(src_video)
        sample_fps = float(params.get("sample_fps", 1.0))
        max_frames = int(params.get("max_frames", 240))
        subtitle_ratio = float(params.get("subtitle_ratio", 0.30))
        min_score = float(params.get("min_score", 0.0))
        roi_diff_thr = float(params.get("roi_diff_thr", 4.0))
        gap_merge = float(params.get("gap_merge_sec", 1.2))
        fix_en_space = bool(params.get("fix_english_space", True))

        step = max(1, int(round(fps / max(sample_fps, 0.0001))))
        idxs = list(range(0, total, step))
        if max_frames and len(idxs) > max_frames:
            n = max_frames
            idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]

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

            jpg_path = os.path.join(frames_dir, f"subtitle_{int(fi):06d}.jpg")
            cv2.imwrite(jpg_path, roi)

            res = ocr.ocr(roi)
            pairs = _extract_texts_from_any(res)
            texts = [txt for (txt, sc) in pairs if txt and float(sc) >= min_score]

            text = _clean_text(" ".join(texts))
            if fix_en_space:
                text = _fix_english_spacing(text)

            if text:
                raw_hits.append({"t": t, "text": text, "key": _norm_sub_key(text), "frame_id": int(fi), "jpg": jpg_path})

            if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                logger.info(f"[{k+1}/{len(idxs)}] frame={fi} hit={1 if text else 0} len={len(text)}")

        cap.release()

        # ✅ 合并相邻相同字幕（按规范化 key 合并）
        segments = []
        for hit in raw_hits:
            if not segments:
                segments.append({
                    "start": hit["t"],
                    "end": hit["t"],
                    "text": hit["text"],
                    "key": hit["key"],
                    "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"], "jpg": hit["jpg"]}],
                })
                continue

            last = segments[-1]
            if hit["key"] == last["key"] and (hit["t"] - last["end"] <= gap_merge):
                last["end"] = hit["t"]
                last["evidence"].append({"t": hit["t"], "frame_id": hit["frame_id"], "jpg": hit["jpg"]})
            else:
                segments.append({
                    "start": hit["t"],
                    "end": hit["t"],
                    "text": hit["text"],
                    "key": hit["key"],
                    "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"], "jpg": hit["jpg"]}],
                })

        # end 往后延一点，srt 更自然
        for seg in segments:
            seg["end"] = float(seg["end"] + max(0.4, 1.0 / max(sample_fps, 0.1)))

        # 输出时不需要 key（但保留也无所谓；你想更干净就删掉）
        json_path = os.path.join(art_dir, "subtitles.json")
        srt_path = os.path.join(art_dir, "subtitles.srt")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
        _write_srt(segments, srt_path)

        logger.info(f"Done. subtitles={len(segments)} srt={srt_path}")
        return {"out_dir": out_dir, "subtitles_json": json_path, "subtitles_srt": srt_path, "count": len(segments)}