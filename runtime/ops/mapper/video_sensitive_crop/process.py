# -*- coding: utf-8 -*-
import json
import os

from datamate.core.base_op import Mapper
from .._video_common.ffmpeg import concat_segments, cut_segment
from .._video_common.io_video import get_video_info
from .._video_common.log import get_logger
from .._video_common.paths import make_run_dir
from ..video_sensitive_detect.process import VideoSensitiveDetect


def complement_intervals(segments, duration):
    if not segments:
        return [[0.0, duration]]

    merged = []
    ordered = sorted([(float(item["start"]), float(item["end"])) for item in segments], key=lambda item: item[0])
    cur_start, cur_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            merged.append([cur_start, cur_end])
            cur_start, cur_end = start, end
    merged.append([cur_start, cur_end])

    keep = []
    prev = 0.0
    for start, end in merged:
        start = max(0.0, min(duration, start))
        end = max(0.0, min(duration, end))
        if start > prev:
            keep.append([prev, start])
        prev = max(prev, end)
    if prev < duration:
        keep.append([prev, duration])
    return [[start, end] for start, end in keep if end - start >= 0.05]


class VideoSensitiveCrop(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample: dict, params: dict = None):
        params = params or self.params
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_sensitive_crop")
        logger = get_logger("VideoSensitiveCrop", log_dir=out_dir)

        segments_json = params.get("segments_json", "")
        if (not segments_json) or (not os.path.exists(segments_json)):
            detect_params = dict(params.get("detect_params", {}) or {})
            for key in ["service_url", "timeout_sec", "sample_fps", "threshold", "merge_gap", "pad_sec", "max_new_tokens"]:
                if key in params and key not in detect_params:
                    detect_params[key] = params[key]

            logger.info("segments_json not provided; run VideoSensitiveDetect first to generate sensitive_segments.json")
            det_out = VideoSensitiveDetect().execute(sample, detect_params)
            for key in ["segments_json", "sensitive_segments_json", "sensitive_segments_path", "json_path", "output_json"]:
                value = det_out.get(key)
                if value and os.path.exists(value):
                    segments_json = value
                    break

            if (not segments_json) or (not os.path.exists(segments_json)):
                fallback = os.path.join(out_dir, "sensitive_segments.json")
                if os.path.exists(fallback):
                    segments_json = fallback
            if (not segments_json) or (not os.path.exists(segments_json)):
                raise RuntimeError("VideoSensitiveCrop: failed to obtain sensitive_segments.json from detect step.")

        keep_mode = str(params.get("keep_mode", "remove")).strip().lower()
        out_name = params.get("out_name") or "cleaned.mp4"
        out_video = os.path.join(out_dir, out_name)

        with open(segments_json, "r", encoding="utf-8") as handle:
            det = json.load(handle)
        segments = det.get("segments", [])

        fps, _, _, nframes = get_video_info(video_path)
        duration = nframes / float(fps) if fps > 0 else 0.0

        if keep_mode == "remove":
            keep_intervals = complement_intervals(segments, duration)
        elif keep_mode == "keep":
            keep_intervals = [[float(item["start"]), float(item["end"])] for item in segments]
        else:
            raise ValueError("keep_mode must be 'remove' or 'keep'")

        logger.info(f"Start crop. mode={keep_mode}, keep_intervals={len(keep_intervals)}, duration={duration:.2f}s")

        if not keep_intervals:
            cut_segment(video_path, out_video, 0.0, duration, logger=logger)
        else:
            seg_dir = os.path.join(out_dir, "segments")
            os.makedirs(seg_dir, exist_ok=True)
            seg_files = []
            for idx, (start, end) in enumerate(keep_intervals):
                seg_path = os.path.join(seg_dir, f"seg_{idx:04d}.mp4")
                cut_segment(video_path, seg_path, start, end, logger=logger)
                seg_files.append(seg_path)
            concat_segments(seg_files, out_video, logger=logger)

        result = {
            "out_dir": out_dir,
            "input": video_path,
            "segments_json": segments_json,
            "keep_mode": keep_mode,
            "output_video": out_video,
            "kept_intervals": keep_intervals,
        }
        json_path = os.path.join(out_dir, "crop_result.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)

        sample.update(result)
        logger.info(f"Done. output={out_video}")
        return sample
