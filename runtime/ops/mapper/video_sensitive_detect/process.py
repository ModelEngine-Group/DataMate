# -*- coding: utf-8 -*-
import os
import json
import cv2

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.qwen_http_client import qwenvl_infer_by_image_path, save_frame_to_jpg


def _merge_times_to_segments(times, gap=1.5, pad=0.5):
    if not times:
        return []
    times = sorted(times)
    segs = []
    s = times[0]
    prev = times[0]
    for t in times[1:]:
        if t - prev <= gap:
            prev = t
        else:
            segs.append([max(0.0, s - pad), prev + pad])
            s = t
            prev = t
    segs.append([max(0.0, s - pad), prev + pad])
    return segs


class VideoSensitiveDetect:
    """
    抽帧 + QwenVL HTTP 敏感检测（对齐 qwen_vl_server.py）：

    服务端：
      POST {service_url}/infer
      JSON: {image_path, task="sensitive", max_new_tokens, language, style}
      返回: {is_sensitive,label,score,reason}

    params:
      - service_url: 默认 http://127.0.0.1:18080
      - timeout_sec: 默认 180
      - sample_fps: 默认 1.0
      - threshold: 默认 0.5
      - merge_gap: 默认 1.5
      - pad_sec: 默认 0.5
      - max_new_tokens: 默认 8
    outputs:
      - out_dir/sensitive_segments.json
    """

    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_sensitive_detect")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger("VideoSensitiveDetect", log_dir)

        service_url = params.get("service_url", "http://127.0.0.1:18080")
        timeout_sec = int(params.get("timeout_sec", 180))
        sample_fps = float(params.get("sample_fps", 1.0))
        threshold = float(params.get("threshold", 0.5))
        merge_gap = float(params.get("merge_gap", 1.5))
        pad_sec = float(params.get("pad_sec", 0.5))
        max_new_tokens = int(params.get("max_new_tokens", 8))

        fps, W, H, total_frames = get_video_info(video_path)
        step = max(1, int(round(float(fps) / max(sample_fps, 1e-6))))

        logger.info(
            f"Start sensitive detect. video={video_path}, fps={fps}, step={step}, "
            f"url={service_url}, thr={threshold}, gap={merge_gap}"
        )

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        hits = []
        sensitive_times = []

        frame_id = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_id % step != 0:
                frame_id += 1
                continue

            t = frame_id / float(fps) if fps else 0.0
            frame_jpg = os.path.join(frames_dir, f"{frame_id:06d}.jpg")
            save_frame_to_jpg(frame, frame_jpg)

            try:
                res = qwenvl_infer_by_image_path(
                    image_path=frame_jpg,
                    task="sensitive",
                    service_url=service_url,
                    max_new_tokens=max_new_tokens,
                    timeout=timeout_sec,
                )
            except Exception as e:
                logger.error(f"infer failed at t={t:.2f}s frame={frame_id}: {repr(e)}")
                frame_id += 1
                continue

            is_sensitive = bool(res.get("is_sensitive", False))
            score = float(res.get("score", 0.0))
            label = str(res.get("label", "none"))
            reason = str(res.get("reason", ""))

            hits.append(
                {
                    "time": t,
                    "frame_idx": frame_id,
                    "image_path": frame_jpg,
                    "is_sensitive": is_sensitive,
                    "label": label,
                    "score": score,
                    "reason": reason,
                }
            )

            if is_sensitive and score >= threshold:
                sensitive_times.append(t)

            frame_id += 1

        cap.release()

        segs = _merge_times_to_segments(sensitive_times, gap=merge_gap, pad=pad_sec)

        result = {
            "out_dir": out_dir,
            "video": video_path,
            "service_url": service_url,
            "sample_fps": sample_fps,
            "threshold": threshold,
            "merge_gap": merge_gap,
            "pad_sec": pad_sec,
            "hits": hits,
            "segments": [{"start": float(s), "end": float(e)} for s, e in segs],
        }

        json_path = os.path.join(out_dir, "sensitive_segments.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. segments_json={json_path}, segments={len(segs)}, hits={len(hits)}")
        return {"out_dir": out_dir, "segments_json": json_path, "segments_count": len(segs)}