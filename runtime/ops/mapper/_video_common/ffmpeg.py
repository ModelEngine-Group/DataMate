# -*- coding: utf-8 -*-
import os
import subprocess

def run_cmd(cmd, logger=None):
    if logger:
        logger.info("FFmpeg cmd: " + " ".join(cmd))
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        msg = f"FFmpeg failed (code={p.returncode}).\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        raise RuntimeError(msg)
    return p.stdout, p.stderr

def convert_to_mp4_h264(
    in_path: str,
    out_path: str,
    crf: int = 23,
    preset: str = "veryfast",
    audio: bool = True,
    fps: int = None,
    scale: str = None,  # e.g. "1280:720" or None
    logger=None,
):
    """
    最通用的“交付格式”：mp4(H.264) + yuv420p
    - crf 越小质量越高，体积越大（18~28常用）
    - preset 越慢压缩越好但越耗时（veryfast/fast/medium）
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    cmd = ["ffmpeg", "-y", "-i", in_path]

    # 视频参数
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", preset, "-crf", str(crf)]

    # 可选 fps / scale
    if fps is not None:
        cmd += ["-r", str(int(fps))]
    if scale is not None:
        cmd += ["-vf", f"scale={scale}"]

    # 音频
    if audio:
        cmd += ["-c:a", "aac", "-b:a", "128k"]
    else:
        cmd += ["-an"]

    cmd += [out_path]
    return run_cmd(cmd, logger=logger)

def transcode_any(
    in_path: str,
    out_path: str,
    vcodec: str = "libx264",
    acodec: str = "aac",
    pix_fmt: str = "yuv420p",
    crf: int = 23,
    preset: str = "veryfast",
    vbitrate: str = None,   # e.g. "2M"
    abitrate: str = "128k",
    fps: int = None,
    scale: str = None,      # e.g. "1280:720"
    extra_args: list = None,
    logger=None,
):
    """
    通用转码：支持任意容器/编码器组合
    - vcodec/acodec 支持 'copy'（封装重打包或直接流拷贝）
    - out_path 后缀决定容器格式：.mp4/.mkv/.mov/.avi/.wmv...
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-i", in_path]

    # video
    cmd += ["-c:v", vcodec]
    if vcodec != "copy":
        cmd += ["-pix_fmt", pix_fmt]
        if crf is not None:
            cmd += ["-crf", str(crf)]
        if preset:
            cmd += ["-preset", preset]
        if vbitrate:
            cmd += ["-b:v", str(vbitrate)]

    # fps/scale
    if fps is not None:
        cmd += ["-r", str(int(fps))]
    if scale is not None:
        cmd += ["-vf", f"scale={scale}"]

    # audio
    cmd += ["-c:a", acodec]
    if acodec != "copy":
        if abitrate:
            cmd += ["-b:a", str(abitrate)]

    if extra_args:
        cmd += list(extra_args)

    cmd += [out_path]
    return run_cmd(cmd, logger=logger)



def cut_segment(in_path: str, out_path: str, start: float, end: float, logger=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-to", str(end), "-i", in_path, "-c", "copy", out_path]
    return run_cmd(cmd, logger=logger)

def concat_segments(segment_paths, out_path: str, logger=None):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    list_file = out_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in segment_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", out_path]
    return run_cmd(cmd, logger=logger)