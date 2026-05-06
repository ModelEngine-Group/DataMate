# -*- coding: utf-8 -*-
import os
import json
import collections
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


class VideoClassifyQwenVL:
    """
    抽帧 + QwenVL HTTP 分类（对齐服务端 task=classify25）：
      返回: {class_id, class_name, raw}

    params:
      - service_url: 默认 http://127.0.0.1:18080
      - timeout_sec: 默认 180
      - sample_fps: 默认 1.0
      - max_frames: 默认 12
      - return_topk: 默认 3
      - max_new_tokens: 默认 16
    outputs:
      - artifacts/classification.json
    """

    def execute(self, sample, params=None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_classify_qwenvl")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))
        logger = get_logger("VideoClassifyQwenVL", log_dir)

        service_url = params.get("service_url", "http://127.0.0.1:18080")
        timeout_sec = int(params.get("timeout_sec", 180))
        sample_fps = float(params.get("sample_fps", 1.0))
        max_frames = int(params.get("max_frames", 12))
        return_topk = int(params.get("return_topk", 3))
        max_new_tokens = int(params.get("max_new_tokens", 16))

        fps, W, H, total_frames = get_video_info(video_path)
        idxs = _sample_frame_indices(total_frames, fps, sample_fps, max_frames)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        votes = collections.Counter()
        evidence = []

        for idx in idxs:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if not ok:
                continue

            frame_jpg = os.path.join(frames_dir, f"{idx:06d}.jpg")
            save_frame_to_jpg(frame, frame_jpg)

            try:
                res = qwenvl_infer_by_image_path(
                    image_path=frame_jpg,
                    task="classify25",
                    service_url=service_url,
                    max_new_tokens=max_new_tokens,
                    timeout=timeout_sec,
                )
            except Exception as e:
                logger.error(f"classify infer failed frame={idx}: {repr(e)}")
                continue

            class_name = (res.get("class_name") or "其他").strip()
            class_id = int(res.get("class_id", 25))
            votes[class_name] += 1
            evidence.append({"frame_idx": idx, "image_path": frame_jpg, "class_id": class_id, "class_name": class_name})

        cap.release()

        topk = [{"label": k, "vote": int(v)} for k, v in votes.most_common(return_topk)]
        top1 = topk[0]["label"] if topk else "其他"

        result = {
            "top1": top1,
            "topk": topk,
            "service_url": service_url,
            "sample_fps": sample_fps,
            "max_frames": max_frames,
            "evidence": evidence,
        }

        json_path = os.path.join(art_dir, "classification.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. classification_json={json_path}, top1={top1}")
        return {"out_dir": out_dir, "classification_json": json_path, "top1": top1}