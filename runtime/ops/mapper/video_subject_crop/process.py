# -*- coding: utf-8 -*-
import json
import os

import cv2

from datamate.core.base_op import Mapper
from .._video_common.log import get_logger
from .._video_common.params import parse_bool
from .._video_common.paths import make_run_dir
from ..video_mot_track.process import VideoMotTrack


def _bbox_area(bbox):
    x1, y1, x2, y2 = bbox
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def _select_top1_track(tracks: dict, min_frames: int = 10):
    stats = {}
    for frame in tracks.get("frames", []):
        for obj in frame.get("objects", []):
            tid = int(obj["track_id"])
            area = _bbox_area(obj["bbox"])
            stats.setdefault(tid, {"count": 0, "area_sum": 0.0})
            stats[tid]["count"] += 1
            stats[tid]["area_sum"] += area

    candidates = []
    for tid, state in stats.items():
        if state["count"] < min_frames:
            continue
        avg_area = state["area_sum"] / max(1, state["count"])
        candidates.append((tid, state["count"], avg_area))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[1], item[2]), reverse=True)
    return int(candidates[0][0])


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _ema(prev_bbox, bbox, alpha=0.8):
    if prev_bbox is None:
        return bbox
    return [
        alpha * prev_bbox[0] + (1 - alpha) * bbox[0],
        alpha * prev_bbox[1] + (1 - alpha) * bbox[1],
        alpha * prev_bbox[2] + (1 - alpha) * bbox[2],
        alpha * prev_bbox[3] + (1 - alpha) * bbox[3],
    ]


def _expand_bbox(bbox, margin, width, height):
    x1, y1, x2, y2 = bbox
    box_w = x2 - x1
    box_h = y2 - y1
    x1 = _clamp(int(x1 - box_w * margin), 0, width - 1)
    y1 = _clamp(int(y1 - box_h * margin), 0, height - 1)
    x2 = _clamp(int(x2 + box_w * margin), 0, width - 1)
    y2 = _clamp(int(y2 + box_h * margin), 0, height - 1)
    if x2 <= x1:
        x2 = min(width - 1, x1 + 1)
    if y2 <= y1:
        y2 = min(height - 1, y1 + 1)
    return [x1, y1, x2, y2]


class VideoSubjectCrop(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample: dict, params: dict = None):
        params = params or self.params
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_subject_crop")
        logger = get_logger("VideoSubjectCrop", log_dir=out_dir)

        tracks_json = params.get("tracks_json")
        if (not tracks_json) or (not os.path.exists(tracks_json)):
            mot_params = dict(params.get("mot_params", {}) or {})
            for key in ["model_root", "yolo_model", "conf", "iou", "classes", "tracker_cfg", "save_debug"]:
                if key in params and key not in mot_params:
                    mot_params[key] = params[key]
            logger.info("tracks_json not provided; run VideoMotTrack first to generate tracks.json")
            mot_out = VideoMotTrack().execute(sample, mot_params)
            tracks_json = mot_out["tracks_json"]

        crop_size = int(params.get("crop_size", 512))
        margin = float(params.get("margin", 0.15))
        smooth_alpha = float(params.get("smooth_alpha", 0.8))
        min_frames = int(params.get("min_frames", 10))
        fill_missing = parse_bool(params.get("fill_missing", False), default=False)

        with open(tracks_json, "r", encoding="utf-8") as handle:
            tracks = json.load(handle)

        fps = float(tracks["fps"])
        width = int(tracks["width"])
        height = int(tracks["height"])

        subject_id = _select_top1_track(tracks, min_frames=min_frames)
        if subject_id is None:
            raise RuntimeError(f"No valid subject track found (min_frames={min_frames}).")

        subjects_dir = os.path.join(out_dir, "subjects")
        os.makedirs(subjects_dir, exist_ok=True)

        with open(os.path.join(subjects_dir, "subject_track_id.txt"), "w", encoding="utf-8") as handle:
            handle.write(str(subject_id))

        out_video = os.path.join(subjects_dir, "subject.mp4")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        writer = cv2.VideoWriter(
            out_video,
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (crop_size, crop_size),
        )

        last_bbox = None
        frame_id = 0
        logger.info(f"Start subject crop. subject_id={subject_id}, tracks={tracks_json}")

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            bbox = None
            if frame_id < len(tracks.get("frames", [])):
                for obj in tracks["frames"][frame_id].get("objects", []):
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

            x1, y1, x2, y2 = _expand_bbox(bbox_s, margin=margin, width=width, height=height)
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                frame_id += 1
                continue

            crop = cv2.resize(crop, (crop_size, crop_size), interpolation=cv2.INTER_LINEAR)
            writer.write(crop)
            frame_id += 1

        cap.release()
        writer.release()

        result = {
            "out_dir": out_dir,
            "subject_track_id": subject_id,
            "subject_video": out_video,
        }
        sample.update(result)
        logger.info(f"Done. subject_video={out_video}")
        return sample
