# -*- coding: utf-8 -*-
import os
import json

from .._video_common.paths import make_run_dir
from .._video_common.log import get_logger
from .._video_common.ffmpeg import run_cmd


class VideoFormatConvert:
    """
    仅做“容器格式转换”（不重编码）：
    - 通过 ffmpeg stream copy 实现：-c:v copy -c:a copy
    - 输出文件后缀决定目标容器格式：mp4/mkv/mov/avi/wmv...

    输入:
      sample["filePath"]
      sample["export_path"]

    params:
      - container: 目标容器后缀（默认 "mp4"）
      - out_name: 输出文件名（默认 "converted.{container}"）
      - copy_video: 是否 copy 视频流（默认 True）
      - copy_audio: 是否 copy 音频流（默认 True）
      - extra_args: 额外 ffmpeg 参数列表（可选）

    输出:
      out_dir/converted.xxx
      out_dir/convert_result.json
      out_dir/run.log
    """

    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        in_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_format_convert")
        logger = get_logger("VideoFormatConvert", log_dir=out_dir)

        # 目标容器
        container = str(params.get("container", "mp4")).lstrip(".").lower()
        out_name = params.get("out_name", f"converted.{container}")
        if not out_name.lower().endswith(f".{container}"):
            # 防止用户给了不匹配的后缀
            out_name = f"{out_name}.{container}"
        out_video = os.path.join(out_dir, out_name)

        copy_video = bool(params.get("copy_video", True))
        copy_audio = bool(params.get("copy_audio", True))
        extra_args = params.get("extra_args", None)  # list[str] or None

        logger.info(f"Start container convert (stream copy). in={in_path}, out={out_video}, container={container}")

        cmd = ["ffmpeg", "-y", "-i", in_path]

        # 视频流
        cmd += ["-c:v", "copy" if copy_video else "libx264"]
        # 音频流
        cmd += ["-c:a", "copy" if copy_audio else "aac"]

        # 如果用户传了额外参数（例如 -map 0、-movflags +faststart 等）
        if extra_args:
            if not isinstance(extra_args, list):
                raise ValueError("params['extra_args'] must be a list, e.g. ['-movflags', '+faststart']")
            cmd += extra_args

        cmd += [out_video]

        try:
            run_cmd(cmd, logger=logger)
        except Exception as e:
            # 给更明确的提示：某些容器不支持某些编码，copy 会失败
            logger.error("Container convert failed. This is usually due to codec/container incompatibility when using stream copy.")
            logger.error("You can either choose a different container, or enable re-encode (copy_video/copy_audio=False).")
            raise

        result = {
            "out_dir": out_dir,
            "input": in_path,
            "output_video": out_video,
            "mode": "stream_copy",
            "params": {
                "container": container,
                "out_name": out_name,
                "copy_video": copy_video,
                "copy_audio": copy_audio,
                "extra_args": extra_args,
            },
        }

        json_path = os.path.join(out_dir, "convert_result.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. output={out_video}")
        return result