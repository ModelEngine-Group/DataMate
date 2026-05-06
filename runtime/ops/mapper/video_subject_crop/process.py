# -*- coding: utf-8 -*-
import os
import json
import cv2

from .._video_common.paths import make_run_dir
from .._video_common.log import get_logger
from ..video_mot_track.process import VideoMotTrack

def _bbox_area(b):
    x1, y1, x2, y2 = b
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)

def _select_top1_track(tracks: dict, min_frames: int = 10):
    stats = {}  # tid -> {"count":int, "area_sum":float}
    for fr in tracks.get("frames", []):
        for obj in fr.get("objects", []):
            tid = int(obj["track_id"])
            area = _bbox_area(obj["bbox"])
            if tid not in stats:
                stats[tid] = {"count": 0, "area_sum": 0.0}
            stats[tid]["count"] += 1
            stats[tid]["area_sum"] += area

    items = []
    for tid, s in stats.items():
        if s["count"] < min_frames:
            continue
        avg_area = s["area_sum"] / max(1, s["count"])
        items.append((tid, s["count"], avg_area))

    if not items:
        return None

    items.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return int(items[0][0])

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

def _ema(prev_bbox, bbox, alpha=0.8):
    if prev_bbox is None:
        return bbox
    return [
        alpha*prev_bbox[0] + (1-alpha)*bbox[0],
        alpha*prev_bbox[1] + (1-alpha)*bbox[1],
        alpha*prev_bbox[2] + (1-alpha)*bbox[2],
        alpha*prev_bbox[3] + (1-alpha)*bbox[3],
    ]

def _expand_bbox(bbox, margin, W, H):
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    x1 = x1 - w * margin
    y1 = y1 - h * margin
    x2 = x2 + w * margin
    y2 = y2 + h * margin
    x1 = _clamp(int(x1), 0, W-1)
    y1 = _clamp(int(y1), 0, H-1)
    x2 = _clamp(int(x2), 0, W-1)
    y2 = _clamp(int(y2), 0, H-1)
    if x2 <= x1: x2 = min(W-1, x1+1)
    if y2 <= y1: y2 = min(H-1, y1+1)
    return [x1, y1, x2, y2]

class VideoSubjectCrop:
    """
    主体追踪裁剪（Top1）：
    输入:
      - sample["filePath"]
      - sample["export_path"]
      - params["tracks_json"] (可选：不提供就自动找同一次 run 的 tracks.json)
    输出:
      - subjects/subject.mp4
      - subjects/subject_track_id.txt
    """
    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_subject_crop")
        logger = get_logger("VideoSubjectCrop", log_dir=out_dir)

        tracks_json = params.get("tracks_json", None)
        if (not tracks_json) or (not os.path.exists(tracks_json)):
            # 自动跑 MOT 生成 tracks.json
            mot_params = params.get("mot_params", {})  # 可选：把 mot 的参数也透传进来
            logger.info("tracks_json not provided; run VideoMotTrack first to generate tracks.json")
            mot_out = VideoMotTrack().execute(sample, mot_params)
            tracks_json = mot_out["tracks_json"]

        crop_size = int(params.get("crop_size", 512))
        margin = float(params.get("margin", 0.15))
        smooth_alpha = float(params.get("smooth_alpha", 0.8))
        min_frames = int(params.get("min_frames", 10))
        fill_missing = bool(params.get("fill_missing", False))

        with open(tracks_json, "r", encoding="utf-8") as f:
            tracks = json.load(f)

        fps = float(tracks["fps"])
        W = int(tracks["width"])
        H = int(tracks["height"])

        subject_id = _select_top1_track(tracks, min_frames=min_frames)
        if subject_id is None:
            raise RuntimeError(f"No valid subject track found (min_frames={min_frames}).")

        subjects_dir = os.path.join(out_dir, "subjects")
        os.makedirs(subjects_dir, exist_ok=True)

        with open(os.path.join(subjects_dir, "subject_track_id.txt"), "w", encoding="utf-8") as f:
            f.write(str(subject_id))

        out_video = os.path.join(subjects_dir, "subject.mp4")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(out_video, fourcc, fps, (crop_size, crop_size))

        last_bbox = None
        frame_id = 0

        logger.info(f"Start subject crop. subject_id={subject_id}, tracks={tracks_json}")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            bbox = None
            if frame_id < len(tracks.get("frames", [])):
                objs = tracks["frames"][frame_id].get("objects", [])
                for obj in objs:
                    if int(obj["track_id"]) == int(subject_id):
                        bbox = obj["bbox"]
                        break

            if bbox is None:
                if fill_missing and last_bbox is not None:
                    bbox_s = last_bbox
                else:
                    frame_id += 1
                    continue
            else:
                bbox_s = _ema(last_bbox, bbox, alpha=smooth_alpha)
                last_bbox = bbox_s

            bbox_e = _expand_bbox(bbox_s, margin=margin, W=W, H=H)
            x1, y1, x2, y2 = bbox_e
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                frame_id += 1
                continue

            crop = cv2.resize(crop, (crop_size, crop_size), interpolation=cv2.INTER_LINEAR)
            writer.write(crop)

            frame_id += 1

        cap.release()
        writer.release()

        logger.info(f"Done. subject_video={out_video}")

        return {
            "out_dir": out_dir,
            "subject_track_id": subject_id,
            "subject_video": out_video,
        }