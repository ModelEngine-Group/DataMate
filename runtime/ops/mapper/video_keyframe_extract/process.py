import os
import re
import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


def _run(cmd: List[str]) -> Tuple[int, str]:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return p.returncode, (p.stderr or "") + (p.stdout or "")


def _ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def _list_jpgs(d: str) -> List[str]:
    if not os.path.isdir(d):
        return []
    xs = [os.path.join(d, x) for x in os.listdir(d) if x.lower().endswith(".jpg")]
    xs.sort()
    return xs


def _probe_duration(ffprobe_path: str, video_path: str) -> float:
    cmd = [
        ffprobe_path, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    rc, out = _run(cmd)
    if rc != 0:
        return 0.0
    try:
        return float(out.strip().splitlines()[-1])
    except Exception:
        return 0.0


def _extract_pts_times_from_showinfo(log_text: str) -> List[float]:
    times: List[float] = []
    pattern = re.compile(r"pts_time:\s*([0-9]+(?:\.[0-9]+)?)")
    for line in log_text.splitlines():
        m = pattern.search(line)
        if m:
            try:
                times.append(float(m.group(1)))
            except Exception:
                pass
    return times


def _pair_files_with_times(files: List[str], times: List[float]) -> List[Tuple[Optional[float], str]]:
    if not files:
        return []

    if not times:
        return [(None, f) for f in files]

    n = min(len(files), len(times))
    pairs = [(times[i], files[i]) for i in range(n)]

    if len(files) > n:
        for i in range(n, len(files)):
            pairs.append((None, files[i]))

    return pairs


@dataclass
class KeyframeParams:
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    scene_threshold: float = 0.3
    threshold_candidates: Optional[List[float]] = None
    max_keyframes: int = 30
    min_interval_sec: float = 1.0
    always_include_first: bool = True
    always_include_last: bool = True
    quality: int = 2
    out_json_name: str = "keyframes.json"


class VideoKeyframeExtractLocal:
    """
    本地运行版：不依赖 datamate。
    输出：
      <out_dir>/artifacts/keyframes/cover.jpg
      <out_dir>/artifacts/keyframes/tail.jpg
      <out_dir>/artifacts/keyframes/%06d.jpg
      <out_dir>/artifacts/keyframes.json
    """

    def run(self, video_path: str, out_dir: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = KeyframeParams(**(params or {}))

        ffmpeg = p.ffmpeg_path or shutil.which("ffmpeg")
        ffprobe = p.ffprobe_path or shutil.which("ffprobe")
        if not ffmpeg:
            raise RuntimeError("ffmpeg not found. Install ffmpeg or set ffmpeg_path.")
        if not ffprobe:
            raise RuntimeError("ffprobe not found. Install ffprobe or set ffprobe_path.")

        artifacts = os.path.join(out_dir, "artifacts")
        key_dir = os.path.join(artifacts, "keyframes")
        _ensure_dir(key_dir)

        duration = _probe_duration(ffprobe, video_path)
        outputs: List[Dict[str, Any]] = []

        # 1) 固定取首帧
        cover_path = os.path.join(key_dir, "cover.jpg")
        if p.always_include_first:
            cmd = [
                ffmpeg, "-hide_banner", "-y",
                "-ss", "0",
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", str(p.quality),
                "-vf", "format=yuvj420p",
                cover_path
            ]
            rc, _ = _run(cmd)
            if rc == 0 and os.path.exists(cover_path):
                outputs.append({"kind": "cover", "time_sec": 0.0, "path": cover_path})

        # 2) 固定取尾帧
        tail_path = os.path.join(key_dir, "tail.jpg")
        tail_time: Optional[float] = None
        if p.always_include_last and duration > 0:
            # 取接近视频末尾的位置，避免有些编码下 duration 精确到末尾会取不到
            tail_time = max(duration - 0.04, 0.0)
            cmd = [
                ffmpeg, "-hide_banner", "-y",
                "-ss", f"{tail_time}",
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", str(p.quality),
                "-vf", "format=yuvj420p",
                tail_path
            ]
            rc, _ = _run(cmd)
            if rc == 0 and os.path.exists(tail_path):
                outputs.append({"kind": "tail", "time_sec": float(tail_time), "path": tail_path})
            else:
                tail_time = None

        # 3) scene keyframes + 真实时间戳
        thr_candidates = p.threshold_candidates or [p.scene_threshold, 0.2, 0.15, 0.1, 0.06]
        scene_pairs: List[Tuple[Optional[float], str]] = []
        used_thr: Optional[float] = None

        for thr in thr_candidates:
            # 清掉旧的 scene 输出（保留 cover / tail）
            for f in _list_jpgs(key_dir):
                base = os.path.basename(f)
                if base not in ("cover.jpg", "tail.jpg"):
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            vf = f"select='gt(scene,{thr})',showinfo,format=yuvj420p"
            out_tpl = os.path.join(key_dir, "%06d.jpg")

            cmd = [
                ffmpeg, "-hide_banner", "-y",
                "-i", video_path,
                "-vf", vf,
                "-q:v", str(p.quality),
                "-frames:v", str(max(p.max_keyframes * 5, 50)),
                "-fps_mode", "vfr",
                out_tpl
            ]
            rc, log = _run(cmd)

            if rc != 0 and "Unrecognized option 'fps_mode'" in log:
                cmd = [
                    ffmpeg, "-hide_banner", "-y",
                    "-i", video_path,
                    "-vf", vf,
                    "-q:v", str(p.quality),
                    "-frames:v", str(max(p.max_keyframes * 5, 50)),
                    "-vsync", "vfr",
                    out_tpl
                ]
                rc, log = _run(cmd)

            files = []
            for f in _list_jpgs(key_dir):
                base = os.path.basename(f)
                if base not in ("cover.jpg", "tail.jpg"):
                    files.append(f)

            pts_times = _extract_pts_times_from_showinfo(log)
            pairs = _pair_files_with_times(files, pts_times)

            if files:
                scene_pairs = pairs
                used_thr = thr
                break

        # 4) fallback：scene=0 时取中间帧
        if not scene_pairs:
            t = duration / 2.0 if duration > 0 else 0.0
            mid_path = os.path.join(key_dir, "000001.jpg")
            cmd = [
                ffmpeg, "-hide_banner", "-y",
                "-ss", f"{t}",
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", str(p.quality),
                "-vf", "format=yuvj420p",
                mid_path
            ]
            rc, log = _run(cmd)
            if rc != 0 or (not os.path.exists(mid_path)):
                raise RuntimeError(
                    f"KeyframeExtractLocal failed: scene=0 and fallback midframe failed. log={log[-800:]}"
                )
            scene_pairs = [(float(t), mid_path)]
            used_thr = None

        # 5) 按真实时间过滤 + 截断 max_keyframes
        kept: List[Tuple[Optional[float], str]] = []
        last_t = -1e9

        for t, f in scene_pairs:
            if t is None:
                kept.append((None, f))
            else:
                if t - last_t >= p.min_interval_sec:
                    kept.append((float(t), f))
                    last_t = t

            if len(kept) >= p.max_keyframes:
                break

        if not kept and scene_pairs:
            kept = [scene_pairs[0]]

        # 6) 先写 outputs，再删除未保留候选帧，保证目录和 json 一致
        kept_paths = set()
        for t, f in kept:
            kept_paths.add(os.path.abspath(f))
            outputs.append({
                "kind": "scene",
                "time_sec": t,
                "path": f
            })

        for f in _list_jpgs(key_dir):
            base = os.path.basename(f)
            if base in ("cover.jpg", "tail.jpg"):
                continue
            if os.path.abspath(f) not in kept_paths:
                try:
                    os.remove(f)
                except Exception:
                    pass

        out_json = os.path.join(artifacts, p.out_json_name)
        payload = {
            "input": video_path,
            "out_dir": out_dir,
            "duration_sec": duration,
            "scene_threshold": p.scene_threshold,
            "used_scene_threshold": used_thr,
            "max_keyframes": p.max_keyframes,
            "min_interval_sec": p.min_interval_sec,
            "always_include_first": p.always_include_first,
            "always_include_last": p.always_include_last,
            "keyframes": outputs,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return {
            "out_dir": out_dir,
            "keyframes_json": out_json,
            "keyframes_dir": key_dir,
        }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--out_dir", required=True)
    ap.add_argument("--scene_threshold", type=float, default=0.15)
    ap.add_argument("--max_keyframes", type=int, default=30)
    ap.add_argument("--min_interval_sec", type=float, default=1.0)
    ap.add_argument("--always_include_first", action="store_true")
    ap.add_argument("--always_include_last", action="store_true")
    args = ap.parse_args()

    runner = VideoKeyframeExtractLocal()
    res = runner.run(
        video_path=args.video,
        out_dir=args.out_dir,
        params={
            "scene_threshold": args.scene_threshold,
            "max_keyframes": args.max_keyframes,
            "min_interval_sec": args.min_interval_sec,
            "always_include_first": bool(args.always_include_first),
            "always_include_last": bool(args.always_include_last),
        },
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))