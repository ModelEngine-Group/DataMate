# -*- coding: utf-8 -*-
import os
import json
import math
import cv2

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.qwen_http_client import qwenvl_infer_by_image_path, save_frame_to_jpg


def _sample_frame_indices(total_frames: int, fps: float, sample_fps: float, max_frames: int):
    if total_frames <= 0:
        return []
    fps = float(fps) if fps else 25.0
    step = max(1, int(round(fps / max(float(sample_fps), 1e-6))))
    idxs = list(range(0, total_frames, step))
    if max_frames and len(idxs) > int(max_frames):
        n = int(max_frames)
        idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]
    return idxs


def _make_montage(frames, cell_w=384, cell_h=216, max_cols=4):
    n = len(frames)
    cols = min(max_cols, n)
    rows = int(math.ceil(n / cols))
    canvas = 255 * (cv2.cvtColor(cv2.UMat(cell_h * rows, cell_w * cols, cv2.CV_8UC3), cv2.COLOR_BGR2RGB).get())
    canvas[:] = 255
    for i, img in enumerate(frames):
        r = i // cols
        c = i % cols
        x0, y0 = c * cell_w, r * cell_h
        resized = cv2.resize(img, (cell_w, cell_h))
        canvas[y0 : y0 + cell_h, x0 : x0 + cell_w] = resized
    return canvas


class VideoSummaryQwenVL:
    """
    抽多帧拼 montage → QwenVL HTTP 生成摘要（对齐服务端 task=summary）：
      返回: {summary}

    params:
      - service_url: 默认 http://127.0.0.1:18080
      - timeout_sec: 默认 180
      - sample_fps: 默认 1.0
      - max_frames: 默认 12
      - language: 默认 zh
      - style: 默认 normal
      - max_new_tokens: 默认 160
      - montage_cell_w: 默认 384
      - montage_cell_h: 默认 216
      - montage_max_cols: 默认 4
    outputs:
      - artifacts/montage.jpg
      - artifacts/summary.json
      - artifacts/frames/*.jpg
    """

    def execute(self, sample, params=None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_summary_qwenvl")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger("VideoSummaryQwenVL", log_dir)

        service_url = params.get("service_url", "http://127.0.0.1:18080")
        timeout_sec = int(params.get("timeout_sec", 180))

        sample_fps = float(params.get("sample_fps", 1.0))
        max_frames = int(params.get("max_frames", 12))
        language = params.get("language", "zh")
        style = params.get("style", "normal")
        max_new_tokens = int(params.get("max_new_tokens", 160))

        cell_w = int(params.get("montage_cell_w", 384))
        cell_h = int(params.get("montage_cell_h", 216))
        max_cols = int(params.get("montage_max_cols", 4))

        fps, W, H, total_frames = get_video_info(video_path)
        idxs = _sample_frame_indices(total_frames, fps, sample_fps, max_frames)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        frames = []
        evidence = []

        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue
            frame_jpg = os.path.join(frames_dir, f"{idx:06d}.jpg")
            save_frame_to_jpg(frame, frame_jpg)
            frames.append(frame)
            evidence.append({"frame_idx": idx, "image_path": frame_jpg})

        cap.release()

        montage_path = os.path.join(art_dir, "montage.jpg")
        summary = ""

        if frames:
            montage = _make_montage(frames, cell_w=cell_w, cell_h=cell_h, max_cols=max_cols)
            cv2.imwrite(montage_path, montage)

            res = qwenvl_infer_by_image_path(
                image_path=montage_path,
                task="summary",
                service_url=service_url,
                max_new_tokens=max_new_tokens,
                language=language,
                style=style,
                timeout=timeout_sec,
            )
            summary = (res.get("summary") or "").strip()

        out_json = os.path.join(art_dir, "summary.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "summary": summary,
                    "service_url": service_url,
                    "sample_fps": sample_fps,
                    "max_frames": max_frames,
                    "language": language,
                    "style": style,
                    "evidence": evidence,
                    "montage": montage_path,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"Done. summary_json={out_json}")
        return {"out_dir": out_dir, "summary_json": out_json, "montage_jpg": montage_path}