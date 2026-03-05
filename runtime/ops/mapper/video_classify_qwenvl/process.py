# -*- coding: utf-8 -*-
import os
import json
import collections
import cv2
import importlib

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info

_qwen = importlib.import_module("tools.qwen_sensitive")
qwenvl_infer = _qwen.qwenvl_infer


CLASS25 = [
    "日常生活", "影视剧集", "音乐舞蹈", "幽默搞笑", "游戏电竞",
    "动漫二次元", "新闻时事", "教育教学", "科技数码", "财经商业",
    "纪录片", "体育竞技", "美食烹饪", "时尚美妆", "汽车交通",
    "萌宠动物", "健康健身", "自然风光", "三农", "监控安防",
    "广告营销", "才艺展示", "军事国防", "情感心理", "其他"
]


def _sample_frame_indices(total_frames: int, fps: float, sample_fps: float, max_frames: int):
    if total_frames <= 0:
        return []
    sample_fps = float(sample_fps)
    fps = float(fps) if fps else 25.0
    step = max(1, int(round(fps / max(sample_fps, 0.0001))))
    idxs = list(range(0, total_frames, step))
    if max_frames and len(idxs) > int(max_frames):
        n = int(max_frames)
        idxs = [idxs[int(i * (len(idxs) - 1) / max(1, n - 1))] for i in range(n)]
    return idxs


class VideoClassifyQwenVL:
    """视频分类（25类）

    思路：抽帧 -> 调 QwenVL 服务 task=classify25 -> 多帧投票输出 top1

    params:
      - sample_fps: float, default 1.0
      - max_frames: int, default 12
      - return_topk: int, default 3
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_classify_qwenvl"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        frames_dir = ensure_dir(os.path.join(art_dir, "frames"))

        logger = get_logger(op_name, log_dir)
        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        fps, w, h, total = get_video_info(video_path)
        sample_fps = float(params.get("sample_fps", 1.0))
        max_frames = int(params.get("max_frames", 12))
        return_topk = int(params.get("return_topk", 3))

        idxs = _sample_frame_indices(total, fps, sample_fps, max_frames)
        logger.info(f"fps={fps:.3f}, frames={total}, sample_fps={sample_fps}, idxs={len(idxs)}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        votes = []
        evidences = []
        for k, fi in enumerate(idxs):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fi))
            ok, frame = cap.read()
            if not ok or frame is None:
                continue

            jpg_path = os.path.join(frames_dir, f"frame_{int(fi):06d}.jpg")
            cv2.imwrite(jpg_path, frame)

            resp = qwenvl_infer(frame, task="classify25", timeout=180)
            cid = int(resp.get("class_id", 25) or 25)
            cname = resp.get("class_name", "其他") or "其他"

            votes.append(cname)
            evidences.append({"frame_id": int(fi), "jpg": jpg_path, "class_id": cid, "class_name": cname})

            logger.info(f"[{k+1}/{len(idxs)}] frame={fi} -> {cid}:{cname}")

        cap.release()

        if not votes:
            result = {"top1": {"class_id": 25, "class_name": "其他", "score": 0.0}, "topk": [], "evidence": []}
        else:
            c = collections.Counter(votes)
            top = c.most_common(max(1, return_topk))
            top1_name, top1_cnt = top[0]
            top1_id = (CLASS25.index(top1_name) + 1) if top1_name in CLASS25 else 25
            result = {
                "top1": {"class_id": int(top1_id), "class_name": top1_name, "score": float(top1_cnt / len(votes))},
                "topk": [{"class_id": (CLASS25.index(name)+1) if name in CLASS25 else 25,
                          "class_name": name, "score": float(cnt / len(votes))} for name, cnt in top],
                "evidence": evidences,
                "meta": {"fps": float(fps), "width": int(w), "height": int(h), "total_frames": int(total)}
            }

        json_path = os.path.join(art_dir, "classification.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. classification_json={json_path}")
        return {"out_dir": out_dir, "classification_json": json_path, "top1": result["top1"]}