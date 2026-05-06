# -*- coding: utf-8 -*-
import os
import json

from .._video_common.paths import make_run_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.ffmpeg import cut_segment, concat_segments
from ..video_sensitive_detect.process import VideoSensitiveDetect


def complement_intervals(segments, duration):
    if not segments:
        return [[0.0, duration]]

    segs = sorted([(float(x["start"]), float(x["end"])) for x in segments], key=lambda x: x[0])

    # merge
    merged = []
    cs, ce = segs[0]
    for s, e in segs[1:]:
        if s <= ce:
            ce = max(ce, e)
        else:
            merged.append([cs, ce])
            cs, ce = s, e
    merged.append([cs, ce])

    keep = []
    prev = 0.0
    for s, e in merged:
        s = max(0.0, min(duration, s))
        e = max(0.0, min(duration, e))
        if s > prev:
            keep.append([prev, s])
        prev = max(prev, e)
    if prev < duration:
        keep.append([prev, duration])

    return [[s, e] for s, e in keep if e - s >= 0.05]


class VideoSensitiveCrop:
    """
    敏感裁剪：默认 remove（剔除敏感段）
    params:
      - segments_json: 必填（video_sensitive_detect 输出）
      - keep_mode: "remove" 或 "keep"（默认 remove）
      - out_name: 默认 cleaned.mp4
    """
    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_sensitive_crop")
        logger = get_logger("VideoSensitiveCrop", log_dir=out_dir)


        segments_json = params.get("segments_json", "")
        # 如果没传 segments_json，就自动先跑 VideoSensitiveDetect 生成
        if (not segments_json) or (not os.path.exists(segments_json)):
            # detect_params 优先从 params["detect_params"] 读取；否则从当前 params 里抽取 detect 所需字段
            detect_params = params.get("detect_params", None)
            if detect_params is None:
                detect_keys = ["qwen_module", "qwen_func", "sample_fps", "threshold", "merge_gap", "prompt"]
                detect_params = {k: params[k] for k in detect_keys if k in params}

            # VideoSensitiveDetect 里 qwen_module 是必填的；没给就明确报错（避免你后面裁剪时不知道为什么没生成）
            if "qwen_module" not in detect_params:
                raise RuntimeError(
                    "VideoSensitiveCrop: segments_json not provided, and detect_params missing required 'qwen_module'. "
                    "Please pass params['qwen_module'] (and optional qwen_func/sample_fps/threshold/merge_gap)."
                )

            logger.info("segments_json not provided; run VideoSensitiveDetect first to generate sensitive_segments.json")
            det_out = VideoSensitiveDetect().execute(sample, detect_params)

            # 兼容不同返回 key：尽量从 det_out 中找出 json 路径
            for key in [
                "segments_json",
                "sensitive_segments_json",
                "sensitive_segments_path",
                "json_path",
                "output_json",
            ]:
                if key in det_out and det_out[key] and os.path.exists(det_out[key]):
                    segments_json = det_out[key]
                    break

            # 如果 detect 没把路径通过 return 带出来，就回退到 out_dir 默认文件名（你的 detect 默认写 sensitive_segments.json）
            if (not segments_json) or (not os.path.exists(segments_json)):
                fallback = os.path.join(out_dir, "sensitive_segments.json")
                if os.path.exists(fallback):
                    segments_json = fallback

            if (not segments_json) or (not os.path.exists(segments_json)):
                raise RuntimeError("VideoSensitiveCrop: failed to obtain sensitive segments json from detect step.")




        keep_mode = params.get("keep_mode", "remove")
        out_name = params.get("out_name", "cleaned.mp4")
        out_video = os.path.join(out_dir, out_name)

        det = json.load(open(segments_json, "r", encoding="utf-8"))
        segments = det.get("segments", [])

        fps, W, H, nframes = get_video_info(video_path)
        duration = nframes / float(fps) if fps > 0 else 0.0

        if keep_mode == "remove":
            keep_intervals = complement_intervals(segments, duration)
        elif keep_mode == "keep":
            keep_intervals = [[float(x["start"]), float(x["end"])] for x in segments]
        else:
            raise ValueError("keep_mode must be 'remove' or 'keep'")

        logger.info(f"Start crop. mode={keep_mode}, keep_intervals={len(keep_intervals)}, duration={duration:.2f}s")

        if not keep_intervals:
            logger.info("No intervals to keep. Copy original as output.")
            cut_segment(video_path, out_video, 0.0, duration, logger=logger)
        else:
            seg_dir = os.path.join(out_dir, "segments")
            os.makedirs(seg_dir, exist_ok=True)

            seg_files = []
            for i, (s, e) in enumerate(keep_intervals):
                seg_path = os.path.join(seg_dir, f"seg_{i:04d}.mp4")
                cut_segment(video_path, seg_path, s, e, logger=logger)
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
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. output={out_video}")
        return result