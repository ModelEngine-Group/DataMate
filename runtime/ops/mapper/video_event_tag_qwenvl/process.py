# -*- coding: utf-8 -*-
import os
import json
import cv2
import importlib

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info

_qwen = importlib.import_module("tools.qwen_sensitive")
qwenvl_infer = _qwen.qwenvl_infer


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


class VideoEventTagQwenVL:
    """事件标注（自适应分段）

    目标（默认参数下）：
      - 8 秒视频 -> 大约 4 段（≈2s/段）
      - 120 秒视频 -> 大约 12 段（≈10s/段）
      - 600 秒视频 -> 大约 12 段（≈50s/段）

    params:
      - adaptive_segment: bool, default True
      - target_segments: int, default 12
      - min_segment_seconds: float, default 2.0
      - max_segment_seconds: float, default 60.0
      - segment_seconds: float, optional（手动覆盖；当 adaptive_segment=False 时使用）
      - max_segments: int, default 60
      - max_new_tokens: int, default 32

    outputs:
      - artifacts/events.json: [{start, end, event, evidence:{frame_id,jpg}}]
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_event_tag_qwenvl"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))

        logger = get_logger(op_name, log_dir)
        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        fps, w, h, total = get_video_info(video_path)
        duration = (total / fps) if fps else 0.0

        adaptive = bool(params.get("adaptive_segment", True))
        target_segments = int(params.get("target_segments", 12))
        min_seg_s = float(params.get("min_segment_seconds", 2.0))
        max_seg_s = float(params.get("max_segment_seconds", 60.0))

        if adaptive:
            # seg_s = duration / target_segments，并 clamp 到[min_seg_s, max_seg_s]
            seg_s = _clamp(duration / max(1, target_segments), min_seg_s, max_seg_s)
        else:
            seg_s = float(params.get("segment_seconds", 5.0))

        max_segments = int(params.get("max_segments", 60))
        max_new_tokens = int(params.get("max_new_tokens", 32))

        logger.info(
            f"fps={fps:.3f}, frames={total}, duration={duration:.2f}s, "
            f"adaptive={adaptive}, segment_seconds={seg_s:.2f}, target_segments={target_segments}"
        )

        if duration <= 0:
            events = []
        else:
            nseg = int(duration // seg_s) + 1
            nseg = min(nseg, max_segments)

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open video: {video_path}")

            events = []
            for i in range(nseg):
                start = i * seg_s
                end = min(duration, (i + 1) * seg_s)
                mid = (start + end) / 2.0
                frame_id = int(mid * fps)

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
                ok, frame = cap.read()
                if not ok or frame is None:
                    continue

                jpg_path = os.path.join(frames_dir, f"seg_{i:03d}_frame_{frame_id:06d}.jpg")
                cv2.imwrite(jpg_path, frame)

                resp = qwenvl_infer(frame, task="event_tag", max_new_tokens=max_new_tokens, timeout=180)
                ev = (resp.get("event") or "").strip()

                events.append({
                    "start": float(start),
                    "end": float(end),
                    "event": ev,
                    "evidence": {"frame_id": int(frame_id), "jpg": jpg_path}
                })

                logger.info(f"[{i+1}/{nseg}] {start:.2f}-{end:.2f} mid={mid:.2f}s -> {ev}")

            cap.release()

        json_path = os.path.join(art_dir, "events.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. events_json={json_path}, segments={len(events)}")
        return {"out_dir": out_dir, "events_json": json_path, "count": len(events), "segment_seconds": float(seg_s)}