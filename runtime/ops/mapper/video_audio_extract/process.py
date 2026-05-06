# -*- coding: utf-8 -*-
import os
import json
import shutil
import subprocess

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger


class VideoAudioExtract:
    """从视频提取音频（wav 16k mono）

    params:
      - ffmpeg_path: str, optional
      - sample_rate: int, default 16000
      - channels: int, default 1
      - out_format: wav|aac, default wav

    outputs:
      - artifacts/audio.wav (or audio.aac)
      - artifacts/audio_info.json
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_audio_extract"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))

        logger = get_logger(op_name, log_dir)
        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg or pass params.ffmpeg_path")

        sr = int(params.get("sample_rate", 16000))
        ch = int(params.get("channels", 1))
        out_format = (params.get("out_format", "wav") or "wav").lower()

        if out_format == "aac":
            audio_path = os.path.join(art_dir, "audio.aac")
            cmd = [
                ffmpeg_path, "-hide_banner", "-y",
                "-i", video_path,
                "-vn",
                "-ac", str(ch),
                "-ar", str(sr),
                "-c:a", "aac",
                audio_path
            ]
        else:
            audio_path = os.path.join(art_dir, "audio.wav")
            cmd = [
                ffmpeg_path, "-hide_banner", "-y",
                "-i", video_path,
                "-vn",
                "-ac", str(ch),
                "-ar", str(sr),
                "-c:a", "pcm_s16le",
                audio_path
            ]

        logger.info("FFmpeg cmd: " + " ".join(cmd))
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"FFmpeg failed (code={p.returncode}).\nSTDERR:\n{p.stderr}")

        info = {"audio_path": audio_path, "sample_rate": sr, "channels": ch, "format": out_format}
        info_path = os.path.join(art_dir, "audio_info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. audio={audio_path}")
        return {"out_dir": out_dir, "audio_path": audio_path, "audio_info": info_path}