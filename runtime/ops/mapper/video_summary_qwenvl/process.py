# -*- coding: utf-8 -*-
import os
import json
import cv2
import math
import importlib
import re

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info

_qwen = importlib.import_module("tools.qwen_sensitive")
qwenvl_infer = _qwen.qwenvl_infer


def _sample_frame_indices(total_frames: int, fps: float, sample_fps: float, max_frames: int):
    """按 sample_fps 抽帧，然后均匀下采样到 max_frames。"""
    if total_frames <= 0:
        return []
    fps = float(fps) if fps else 25.0
    step = max(1, int(round(fps / max(float(sample_fps), 0.0001))))
    idxs = list(range(0, total_frames, step))
    if max_frames and len(idxs) > int(max_frames):
        n = int(max_frames)
        idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]
    return idxs


def _make_montage(frames_bgr, cell_w=384, cell_h=216, max_cols=4, bg=0):
    """把多帧拼成一张图（montage），用于“基于多帧生成总摘要”。
    - frames_bgr: List[np.ndarray(BGR)]
    """
    if not frames_bgr:
        return None

    n = len(frames_bgr)
    cols = min(max_cols, n)
    rows = int(math.ceil(n / cols))

    montage = (bg * np.ones((rows * cell_h, cols * cell_w, 3), dtype=frames_bgr[0].dtype))  # noqa

    for i, fr in enumerate(frames_bgr):
        r = i // cols
        c = i % cols
        # resize to cell
        fr_r = cv2.resize(fr, (cell_w, cell_h), interpolation=cv2.INTER_AREA)
        y0 = r * cell_h
        x0 = c * cell_w
        montage[y0:y0 + cell_h, x0:x0 + cell_w] = fr_r

    return montage


def _squeeze_whitespace(text: str) -> str:
    """把多余空白（包括 \\n）压成一个空格，变成“一段话”更易读。"""
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    return t


# numpy 在 montage 中用到（避免你环境里没装导致 import 报错：你现在 qwen 环境肯定有 numpy，但 datamate 环境也应有）
import numpy as np  # noqa: E402


class VideoSummaryQwenVL:
    """视频文本概括（QwenVL，多帧总摘要）

    核心：抽多帧 -> 拼成 montage -> 只调用一次 task=summary -> 得到“总摘要”

    params:
      - sample_fps: float, default 1.0
      - max_frames: int, default 12
      - language: zh|en, default zh
      - style: short|normal|detail, default normal
      - max_new_tokens: int, default 160
      - montage_cell_w: int, default 384
      - montage_cell_h: int, default 216
      - montage_max_cols: int, default 4

    outputs:
      - artifacts/summary.json: {summary, evidence:[{frame_id,jpg}], montage_jpg}
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_summary_qwenvl"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))

        logger = get_logger(op_name, log_dir)
        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        fps, w, h, total = get_video_info(video_path)

        sample_fps = float(params.get("sample_fps", 1.0))
        max_frames = int(params.get("max_frames", 12))
        language = params.get("language", "zh")
        style = params.get("style", "normal")
        max_new_tokens = int(params.get("max_new_tokens", 160))

        cell_w = int(params.get("montage_cell_w", 384))
        cell_h = int(params.get("montage_cell_h", 216))
        max_cols = int(params.get("montage_max_cols", 4))

        idxs = _sample_frame_indices(total, fps, sample_fps, max_frames)
        logger.info(f"fps={fps:.3f}, frames={total}, idxs={len(idxs)}, style={style}, lang={language}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        frames_for_montage = []
        evidence = []

        for k, fi in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            jpg_path = os.path.join(frames_dir, f"frame_{int(fi):06d}.jpg")
            cv2.imwrite(jpg_path, frame)

            frames_for_montage.append(frame)
            evidence.append({"frame_id": int(fi), "jpg": jpg_path})

            logger.info(f"[{k+1}/{len(idxs)}] frame={fi} collected")

        cap.release()

        montage = _make_montage(frames_for_montage, cell_w=cell_w, cell_h=cell_h, max_cols=max_cols, bg=0)
        if montage is None:
            result = {
                "summary": "",
                "evidence": evidence,
                "montage_jpg": "",
                "meta": {"fps": float(fps), "width": int(w), "height": int(h), "total_frames": int(total)}
            }
        else:
            montage_path = os.path.join(art_dir, "montage.jpg")
            cv2.imwrite(montage_path, montage)

            # ✅ 只调用一次：基于“多帧拼图”生成总摘要
            resp = qwenvl_infer(
                montage,
                task="summary",
                language=language,
                style=style,
                max_new_tokens=max_new_tokens,
                timeout=180,
            )
            summary = _squeeze_whitespace((resp.get("summary") or "").strip())

            result = {
                "summary": summary,
                "evidence": evidence,
                "montage_jpg": montage_path,
                "meta": {"fps": float(fps), "width": int(w), "height": int(h), "total_frames": int(total)}
            }

        json_path = os.path.join(art_dir, "summary.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. summary_json={json_path}, summary_len={len(result.get('summary',''))}")
        return {"out_dir": out_dir, "summary_json": json_path, "summary": result.get("summary", "")}