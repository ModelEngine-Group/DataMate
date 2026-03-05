# -*- coding: utf-8 -*-
import os
import json
import importlib
import cv2

from .._video_common.paths import make_run_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info


def merge_times_to_segments(times, gap=1.5):
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
            segs.append([max(0.0, s - 0.5), prev + 0.5])
            s = t
            prev = t
    segs.append([max(0.0, s - 0.5), prev + 0.5])
    return segs


class VideoSensitiveDetect:
    """
    简单敏感检测（抽帧 + Qwen判定）：
    必填 params:
      - qwen_module: 例如 "tools.qwen_sensitive"
      - qwen_func:   例如 "sensitive_infer"

    可选 params:
      - sample_fps: 默认 1
      - threshold: 默认 0.5
      - merge_gap: 默认 1.5
      - prompt: 要求模型输出 JSON 的提示词
    """
    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_sensitive_detect")
        logger = get_logger("VideoSensitiveDetect", log_dir=out_dir)

        qwen_module = params.get("qwen_module")
        qwen_func = params.get("qwen_func", "sensitive_infer")
        if not qwen_module:
            raise RuntimeError("params['qwen_module'] is required, e.g. 'tools.qwen_sensitive'")

        mod = importlib.import_module(qwen_module)
        if not hasattr(mod, qwen_func):
            raise RuntimeError(f"Function '{qwen_func}' not found in module '{qwen_module}'")
        infer_fn = getattr(mod, qwen_func)

        sample_fps = float(params.get("sample_fps", 1.0))
        threshold = float(params.get("threshold", 0.5))
        merge_gap = float(params.get("merge_gap", 1.5))
        prompt = params.get(
            "prompt",
            "内容审核：若画面含色情/裸露、明显血腥流血、尸体、爆炸火光、持枪打斗、恐怖暴力、政治人物/政治标语，则判违规。"
            "只输出JSON：{\"is_sensitive\":true/false,\"label\":\"porn|violence|blood|explosion|politics|none\",\"score\":0~1,\"reason\":\"一句话\"}"
        )

        fps, W, H, nframes = get_video_info(video_path)
        step = max(1, int(round(fps / sample_fps)))

        logger.info(f"Start sensitive detect. video={video_path}, fps={fps}, sample_fps={sample_fps}, step={step}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        hits = []
        times = []

        frame_id = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_id % step != 0:
                frame_id += 1
                continue

            t = frame_id / float(fps)

            try:
                res = infer_fn(frame, prompt)
            except Exception as e:
                logger.error(f"infer failed at t={t:.2f}: {e}")
                frame_id += 1
                continue

            is_sensitive = bool(res.get("is_sensitive", False))
            score = float(res.get("score", 0.0))
            label = str(res.get("label", "unknown"))
            reason = str(res.get("reason", ""))

            hits.append({"time": t, "is_sensitive": is_sensitive, "score": score, "label": label, "reason": reason})

            if is_sensitive and score >= threshold:
                times.append(t)

            frame_id += 1

        cap.release()

        segs = merge_times_to_segments(times, gap=merge_gap)

        result = {
            "out_dir": out_dir,
            "video": video_path,
            "sample_fps": sample_fps,
            "threshold": threshold,
            "merge_gap": merge_gap,
            "hits": hits,
            "segments": [{"start": float(s), "end": float(e)} for s, e in segs],
        }

        json_path = os.path.join(out_dir, "sensitive_segments.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. segments_json={json_path}, segments={len(segs)}, hits={len(hits)}")

        return {
            "out_dir": out_dir,
            "segments_json": json_path,
            "segments_count": len(segs),
            "hits_count": len(hits),
        }