# -*- coding: utf-8 -*-
import os
import json
import re
import shutil
import subprocess
from difflib import SequenceMatcher
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
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+([,.;:?!])", r"\1", t)
    t = re.sub(r"([,.;:?!])([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _norm_sub_key(text: str) -> str:
    """原始 key：保守，仅用于展示/回溯"""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[.。!?！？]+$", "", t).strip()
    if _english_ratio(t) > 0.40:
        t = t.lower()
    return t


def _merge_norm_text(text: str) -> str:
    """用于合并判断的更强规范化。
    英文：小写、去大部分标点、压缩空格，额外生成 nospace 判断。
    中文：保留汉字和数字，去尾部标点的影响。
    """
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    # 去掉中英文尾标点影响
    t = re.sub(r"[.。,，!！?？:：;；~～_\-]+$", "", t).strip()
    # 中间的特殊符号尽量弱化
    t = re.sub(r"[^0-9a-z\u4e00-\u9fff\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _merge_nospace_text(text: str) -> str:
    t = _merge_norm_text(text)
    t = re.sub(r"\s+", "", t)
    return t


def _text_sim(a: str, b: str) -> float:
    a1 = _merge_nospace_text(a)
    b1 = _merge_nospace_text(b)
    if not a1 or not b1:
        return 0.0
    if a1 == b1:
        return 1.0
    return SequenceMatcher(None, a1, b1).ratio()


def _choose_better_text(a: str, b: str) -> str:
    """相似字幕合并时，保留更像完整句子的版本。"""
    if not a:
        return b
    if not b:
        return a
    a_score = len(_merge_nospace_text(a))
    b_score = len(_merge_nospace_text(b))
    # 有明显结束标点的稍微加分
    if re.search(r"[.。!?！？]$", a.strip()):
        a_score += 2
    if re.search(r"[.。!?！？]$", b.strip()):
        b_score += 2
    return b if b_score > a_score else a


def _should_merge_hit(last_seg, hit, gap_merge: float, sim_thr: float = 0.90) -> bool:
    dt = hit["t"] - last_seg["end"]
    if dt > gap_merge:
        return False

    # 1) 原始 key 一样
    if hit["key"] == last_seg["key"]:
        return True

    # 2) 更强的规范化后完全一致（尤其适合英文空格/标点变化）
    if _merge_nospace_text(hit["text"]) == _merge_nospace_text(last_seg["text"]):
        return True

    # 3) 一方是另一方的子串，且时间很近
    a = _merge_nospace_text(last_seg["text"])
    b = _merge_nospace_text(hit["text"])
    if a and b and (a in b or b in a) and dt <= max(2.0, gap_merge):
        return True

    # 4) 文本相似度高，则认为是同一句的 OCR 波动
    sim = _text_sim(last_seg["text"], hit["text"])
    if sim >= sim_thr:
        return True

    return False


def _post_merge_segments(segments, gap_merge: float):
    """第二轮后处理：处理 A, A', A'' 这类连续波动；必要时删除极短重复段。"""
    if not segments:
        return segments

    merged = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if _should_merge_hit(last, {"t": seg["start"], "text": seg["text"], "key": seg.get("key", "")}, gap_merge=max(gap_merge, 2.0), sim_thr=0.86):
            last["end"] = max(last["end"], seg["end"])
            last["text"] = _choose_better_text(last["text"], seg["text"])
            last["key"] = _norm_sub_key(last["text"])
            last.setdefault("evidence", []).extend(seg.get("evidence", []))
        else:
            merged.append(seg)

    # 删除明显的短抖动重复：前后两段极近且文本高度相似，保留更优那一段
    cleaned = []
    for seg in merged:
        if not cleaned:
            cleaned.append(seg)
            continue
        last = cleaned[-1]
        sim = _text_sim(last["text"], seg["text"])
        if sim >= 0.92 and (seg["start"] - last["end"] <= max(2.0, gap_merge)):
            last["end"] = max(last["end"], seg["end"])
            last["text"] = _choose_better_text(last["text"], seg["text"])
            last["key"] = _norm_sub_key(last["text"])
            last.setdefault("evidence", []).extend(seg.get("evidence", []))
        else:
            cleaned.append(seg)
    return cleaned


def _roi_changed(cur_roi, last_roi, diff_thr=4.0):
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


class VideoSubtitleOCR:
    """字幕 OCR（增强版相邻重复合并）"""

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
        gap_merge = float(params.get("gap_merge_sec", 2.0))
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
                raw_hits.append({
                    "t": t,
                    "text": text,
                    "key": _norm_sub_key(text),
                    "frame_id": int(fi),
                    "jpg": jpg_path
                })

            if (k + 1) % 20 == 0 or k == len(idxs) - 1:
                logger.info(f"[{k+1}/{len(idxs)}] frame={fi} hit={1 if text else 0} len={len(text)}")

        cap.release()

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
            if _should_merge_hit(last, hit, gap_merge=gap_merge, sim_thr=0.90):
                last["end"] = hit["t"]
                last["text"] = _choose_better_text(last["text"], hit["text"])
                last["key"] = _norm_sub_key(last["text"])
                last["evidence"].append({"t": hit["t"], "frame_id": hit["frame_id"], "jpg": hit["jpg"]})
            else:
                segments.append({
                    "start": hit["t"],
                    "end": hit["t"],
                    "text": hit["text"],
                    "key": hit["key"],
                    "evidence": [{"t": hit["t"], "frame_id": hit["frame_id"], "jpg": hit["jpg"]}],
                })

        segments = _post_merge_segments(segments, gap_merge=gap_merge)

        for seg in segments:
            seg["end"] = float(seg["end"] + max(0.4, 1.0 / max(sample_fps, 0.1)))

        json_path = os.path.join(art_dir, "subtitles.json")
        srt_path = os.path.join(art_dir, "subtitles.srt")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
        _write_srt(segments, srt_path)

        logger.info(f"Done. subtitles={len(segments)} srt={srt_path}")
        return {
            "out_dir": out_dir,
            "subtitles_json": json_path,
            "subtitles_srt": srt_path,
            "count": len(segments)
        }
