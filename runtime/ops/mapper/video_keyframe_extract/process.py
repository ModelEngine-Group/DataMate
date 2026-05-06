import os
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
    # 尽量不用任何第三方库，直接 ffprobe
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


@dataclass
class KeyframeParams:
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    scene_threshold: float = 0.3
    threshold_candidates: Optional[List[float]] = None
    max_keyframes: int = 30
    min_interval_sec: float = 1.0
    always_include_first: bool = True
    quality: int = 2  # -q:v
    out_json_name: str = "keyframes.json"


class VideoKeyframeExtractLocal:
    """
    本地运行版：不依赖 datamate。
    输出：
      <out_dir>/artifacts/keyframes/cover.jpg (可选)
      <out_dir>/artifacts/keyframes/%06d.jpg  (scene 帧)
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

        # 1) cover
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
            rc, log = _run(cmd)
            if rc == 0 and os.path.exists(cover_path):
                outputs.append({"kind": "cover", "time_sec": 0.0, "path": cover_path})
            else:
                # cover 失败不致命
                pass

        # 2) scene keyframes
        thr_candidates = p.threshold_candidates or [p.scene_threshold, 0.2, 0.15, 0.1, 0.06]
        scene_files: List[str] = []
        used_thr: Optional[float] = None

        for thr in thr_candidates:
            # 清掉旧的 scene 输出（保留 cover）
            for f in _list_jpgs(key_dir):
                if os.path.basename(f) != "cover.jpg":
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            vf = f"select='gt(scene,{thr})',format=yuvj420p"
            out_tpl = os.path.join(key_dir, "%06d.jpg")

            # 兼容新旧 ffmpeg
            cmd = [
                ffmpeg, "-hide_banner", "-y",
                "-i", video_path,
                "-vf", vf,
                "-q:v", str(p.quality),
                "-frames:v", str(p.max_keyframes * 3),
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
                    "-frames:v", str(p.max_keyframes * 3),
                    "-vsync", "vfr",
                    out_tpl
                ]
                rc, log = _run(cmd)

            files = [f for f in _list_jpgs(key_dir) if os.path.basename(f) != "cover.jpg"]
            if files:
                scene_files = files
                used_thr = thr
                break

        # 3) fallback：scene=0 时取中间帧
        if not scene_files:
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
                raise RuntimeError(f"KeyframeExtractLocal failed: scene=0 and fallback midframe failed. log={log[-800:]}")
            scene_files = [mid_path]
            used_thr = None

        # 4) 时间间隔过滤 + 截断 max_keyframes
        # 这里用“均匀估计”时间戳（不解析 showinfo），足够用于过滤过密
        if duration > 0 and len(scene_files) > 1:
            kept: List[Tuple[float, str]] = []
            last_t = -1e9
            for i, f in enumerate(scene_files):
                t = (i / max(1, (len(scene_files) - 1))) * duration
                if t - last_t >= p.min_interval_sec:
                    kept.append((t, f))
                    last_t = t
                if len(kept) >= p.max_keyframes:
                    break
            for t, f in kept:
                outputs.append({"kind": "scene", "time_sec": float(t), "path": f})
        else:
            for f in scene_files[:p.max_keyframes]:
                outputs.append({"kind": "scene", "time_sec": None, "path": f})

        out_json = os.path.join(artifacts, p.out_json_name)
        payload = {
            "input": video_path,
            "out_dir": out_dir,
            "scene_threshold": p.scene_threshold,
            "used_scene_threshold": used_thr,
            "max_keyframes": p.max_keyframes,
            "min_interval_sec": p.min_interval_sec,
            "always_include_first": p.always_include_first,
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
        },
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))