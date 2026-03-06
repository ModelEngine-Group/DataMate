# -*- coding: utf-8 -*-
import os
import json
import cv2

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.qwen_http_client import qwenvl_infer_by_image_path, save_frame_to_jpg


def _make_segments(duration_sec: float, params: dict):
    adaptive = bool(params.get("adaptive_segment", True))
    max_segments = int(params.get("max_segments", 60))
    max_new_tokens = int(params.get("max_new_tokens", 32))

    if duration_sec <= 0:
        return [(0.0, 0.0)]

    if not adaptive:
        seg_len = float(params.get("segment_seconds", 5.0))
    else:
        target = int(params.get("target_segments", 12))
        min_seg = float(params.get("min_segment_seconds", 2.0))
        max_seg = float(params.get("max_segment_seconds", 60.0))
        seg_len = duration_sec / max(1, target)
        seg_len = max(min_seg, min(max_seg, seg_len))

    segs = []
    s = 0.0
    while s < duration_sec and len(segs) < max_segments:
        e = min(duration_sec, s + seg_len)
        segs.append((s, e))
        s = e
    return segs


class VideoEventTagQwenVL:
    """
    分段取中点帧 → QwenVL HTTP 事件标注（对齐服务端 task=event_tag）：
      返回: {event}

    params:
      - service_url: 默认 http://127.0.0.1:18080
      - timeout_sec: 默认 180
      - adaptive_segment: 默认 True
      - target_segments: 默认 12
      - min_segment_seconds: 默认 2.0
      - max_segment_seconds: 默认 60.0
      - segment_seconds: 默认 5.0（当 adaptive_segment=false 时）
      - max_segments: 默认 60
      - max_new_tokens: 默认 32
    outputs:
      - artifacts/events.json
      - artifacts/frames/*.jpg
    """

    def execute(self, sample, params=None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_event_tag_qwenvl")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger("VideoEventTagQwenVL", log_dir)

        service_url = params.get("service_url", "http://127.0.0.1:18080")
        timeout_sec = int(params.get("timeout_sec", 180))
        max_new_tokens = int(params.get("max_new_tokens", 32))

        fps, W, H, total_frames = get_video_info(video_path)
        duration_sec = (float(total_frames) / float(fps)) if fps else 0.0
        segs = _make_segments(duration_sec, params)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        events = []
        for i, (s, e) in enumerate(segs):
            mid = (s + e) / 2.0
            mid_frame = int(round(mid * float(fps))) if fps else 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
            ok, frame = cap.read()
            if not ok:
                continue

            frame_jpg = os.path.join(frames_dir, f"seg_{i:04d}_mid_{mid_frame:06d}.jpg")
            save_frame_to_jpg(frame, frame_jpg)

            try:
                res = qwenvl_infer_by_image_path(
                    image_path=frame_jpg,
                    task="event_tag",
                    service_url=service_url,
                    max_new_tokens=max_new_tokens,
                    timeout=timeout_sec,
                )
                event = (res.get("event") or "").strip()
            except Exception as ex:
                logger.error(f"event_tag infer failed seg={i} mid={mid:.2f}: {repr(ex)}")
                event = ""

            events.append(
                {
                    "seg_id": i,
                    "start": float(s),
                    "end": float(e),
                    "mid": float(mid),
                    "mid_frame": int(mid_frame),
                    "image_path": frame_jpg,
                    "event": event,
                }
            )

        cap.release()

        out_json = os.path.join(art_dir, "events.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "video": video_path,
                    "service_url": service_url,
                    "duration_sec": duration_sec,
                    "segments": events,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        logger.info(f"Done. events_json={out_json}, segments={len(events)}")
        return {"out_dir": out_dir, "events_json": out_json, "segments_count": len(events)}