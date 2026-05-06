# -*- coding: utf-8 -*-
import os
import re
import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger


@dataclass
class CropBox:
    w: int
    h: int
    x: int
    y: int

    def to_str(self) -> str:
        return f"{self.w}:{self.h}:{self.x}:{self.y}"


def _even(x: int) -> int:
    return x - (x % 2)


def _parse_cropdetect(stderr: str) -> List[CropBox]:
    # ffmpeg cropdetect logs like: "crop=iw:ih:x:y" or "crop=1920:800:0:140"
    boxes = []
    for line in stderr.splitlines():
        m = re.search(r"crop=(\d+):(\d+):(\d+):(\d+)", line)
        if m:
            w, h, x, y = map(int, m.groups())
            boxes.append(CropBox(w=w, h=h, x=x, y=y))
    return boxes


def _pick_box(boxes: List[CropBox], mode: str = "safe_keep_more") -> Optional[CropBox]:
    """
    mode:
      - safe_keep_more: 尽量少裁（更保守，避免误裁内容）=> 取 w/h 最大 + x/y 最小
      - aggressive_remove_more: 尽量多裁黑边 => 取 w/h 最小 + x/y 最大
      - median: 取中位数
    """
    if not boxes:
        return None

    ws = sorted(b.w for b in boxes)
    hs = sorted(b.h for b in boxes)
    xs = sorted(b.x for b in boxes)
    ys = sorted(b.y for b in boxes)

    if mode == "aggressive_remove_more":
        w, h, x, y = min(ws), min(hs), max(xs), max(ys)
    elif mode == "median":
        mid = len(ws) // 2
        w, h, x, y = ws[mid], hs[mid], xs[mid], ys[mid]
    else:
        # 默认：尽量少裁，避免裁掉内容
        w, h, x, y = max(ws), max(hs), min(xs), min(ys)

    # crop 参数通常要求偶数（编码器/像素格式更兼容）
    return CropBox(w=_even(w), h=_even(h), x=_even(x), y=_even(y))


def detect_crop_box(
    ffmpeg_path: str,
    video_path: str,
    sample_points: List[Tuple[float, float]],
    cropdetect: str,
    logger,
) -> Optional[CropBox]:
    """在多个时间点探测 crop，汇总后给出一个 crop box。"""
    all_boxes: List[CropBox] = []
    for (ss, dur) in sample_points:
        cmd = [
            ffmpeg_path, "-hide_banner", "-y",
            "-ss", f"{ss}",
            "-i", video_path,
            "-t", f"{dur}",
            "-vf", cropdetect,
            "-f", "null", "-"
        ]
        logger.info("cropdetect cmd: " + " ".join(cmd))
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # cropdetect 输出在 stderr；即使 returncode!=0 也可能有输出，所以不直接失败
        boxes = _parse_cropdetect(p.stderr)
        if boxes:
            # 取该段最后一个（通常更稳定）
            all_boxes.append(boxes[-1])

    # 汇总选择一个 box（默认保守：少裁）
    return _pick_box(all_boxes, mode="safe_keep_more")


def crop_video(
    ffmpeg_path: str,
    video_path: str,
    out_path: str,
    crop: CropBox,
    logger,
    crf: int = 23,
    preset: str = "veryfast",
    audio_copy: bool = True,
):
    # 裁剪会改变尺寸，必须重新编码视频；音频可以 copy
    cmd = [
        ffmpeg_path, "-hide_banner", "-y",
        "-i", video_path,
        "-vf", f"crop={crop.to_str()}",
        "-c:v", "libx264",
        "-preset", preset,
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
    ]
    if audio_copy:
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", "128k"]

    cmd += [out_path]

    logger.info("crop cmd: " + " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg crop failed (code={p.returncode}).\nSTDERR:\n{p.stderr}")


class VideoDeborderCrop:
    """去黑边（自动 cropdetect + crop）

    params:
      - ffmpeg_path: str, optional
      - cropdetect: str, default "cropdetect=24:16:0"
      - sample_points: list, optional
          默认会采样 [(0,2),(5,2)]；如果视频很短也没关系
      - force_crop: str, optional  # 直接指定 "w:h:x:y"
      - crf: int, default 23
      - preset: str, default "veryfast"
      - audio_copy: bool, default True

    outputs:
      - artifacts/deborder.mp4
      - artifacts/crop_params.json
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_deborder_crop"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        logger = get_logger(op_name, log_dir)

        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg or pass params.ffmpeg_path")

        cropdetect = params.get("cropdetect", "cropdetect=24:16:0")
        force_crop = params.get("force_crop", None)
        crf = int(params.get("crf", 23))
        preset = params.get("preset", "veryfast")
        audio_copy = bool(params.get("audio_copy", True))

        # 默认采样点：开头 2s + 5s 处 2s
        sample_points = params.get("sample_points", None)
        if not sample_points:
            sample_points = [(0.0, 2.0), (5.0, 2.0)]

        crop_box: Optional[CropBox] = None
        if force_crop:
            m = re.match(r"(\d+):(\d+):(\d+):(\d+)", str(force_crop))
            if not m:
                raise ValueError('force_crop must be "w:h:x:y"')
            w, h, x, y = map(int, m.groups())
            crop_box = CropBox(w=_even(w), h=_even(h), x=_even(x), y=_even(y))
        else:
            crop_box = detect_crop_box(ffmpeg_path, video_path, sample_points, cropdetect, logger)

        if not crop_box:
            # 探测不到就原样输出（不裁剪）
            logger.warning("cropdetect found nothing, keep original video.")
            crop_box = CropBox(w=0, h=0, x=0, y=0)

        out_mp4 = os.path.join(art_dir, "deborder.mp4")
        crop_json = os.path.join(art_dir, "crop_params.json")

        if crop_box.w == 0 or crop_box.h == 0:
            # 直接复制（不裁）
            cmd = [ffmpeg_path, "-hide_banner", "-y", "-i", video_path, "-c", "copy", out_mp4]
            logger.info("copy cmd: " + " ".join(cmd))
            p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if p.returncode != 0:
                raise RuntimeError(f"ffmpeg copy failed (code={p.returncode}).\nSTDERR:\n{p.stderr}")
            info = {"mode": "copy", "crop": None, "out_mp4": out_mp4}
        else:
            crop_video(ffmpeg_path, video_path, out_mp4, crop_box, logger, crf=crf, preset=preset, audio_copy=audio_copy)
            info = {"mode": "crop", "crop": crop_box.__dict__, "out_mp4": out_mp4}

        with open(crop_json, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. deborder_mp4={out_mp4}")
        return {"out_dir": out_dir, "deborder_mp4": out_mp4, "crop_params_json": crop_json}