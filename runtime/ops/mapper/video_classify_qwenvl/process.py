# -*- coding: utf-8 -*-
import os
import json
import collections
import cv2

from datamate.core.base_op import Mapper
from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.qwen_http_client import qwenvl_infer_by_image_path, resolve_qwenvl_service_url


CLASS_NAMES = [
    "影视剧情类", "新闻资讯类", "教育知识类", "美食饮品类", "自然风光类",
    "时尚美妆类", "亲子育儿类", "宠物日常类", "游戏电竞类", "音乐舞蹈类",
    "动漫二次元类", "数码产品类", "汽车交通类", "财经商业类", "文化艺术类",
    "乐器演奏类", "国防军事类", "体育竞技类", "野生动物类", "农业类",
    "航空航天类", "其他类"
]

DEFAULT_CLASS_ID = len(CLASS_NAMES)
DEFAULT_CLASS_NAME = CLASS_NAMES[-1]


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


class VideoClassifyQwenVL(Mapper):
    """视频分类

    思路：抽帧 -> 调 QwenVL 服务做 22 类分类 -> 多帧投票输出 top1

    说明：
      - 当前服务端线上接口名仍兼容使用 legacy task "classify25"
      - 但返回的类别集合按当前 22 类版本进行解释

    params:
      - sample_fps: float, default 1.0
      - max_frames: int, default 12
      - return_topk: int, default 3
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample, params=None):
        params = params or self.params
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
        service_url = resolve_qwenvl_service_url(params.get("service_url"))
        timeout_sec = int(params.get("timeout_sec", 180))

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

            resp = qwenvl_infer_by_image_path(
                image_path=jpg_path,
                task="classify25",
                service_url=service_url,
                max_new_tokens=16,
                timeout=timeout_sec,
            )
            cid = int(resp.get("class_id", DEFAULT_CLASS_ID) or DEFAULT_CLASS_ID)
            if 1 <= cid <= len(CLASS_NAMES):
                cname = CLASS_NAMES[cid - 1]
            else:
                cid = DEFAULT_CLASS_ID
                cname = DEFAULT_CLASS_NAME

            votes.append(cname)
            evidences.append({"frame_id": int(fi), "jpg": jpg_path, "class_id": cid, "class_name": cname})

            logger.info(f"[{k+1}/{len(idxs)}] frame={fi} -> {cid}:{cname}")

        cap.release()

        if not votes:
            result = {
                "top1": {"class_id": DEFAULT_CLASS_ID, "class_name": DEFAULT_CLASS_NAME, "score": 0.0},
                "topk": [],
                "evidence": []
            }
        else:
            c = collections.Counter(votes)
            top = c.most_common(max(1, return_topk))
            top1_name, top1_cnt = top[0]
            top1_id = (CLASS_NAMES.index(top1_name) + 1) if top1_name in CLASS_NAMES else DEFAULT_CLASS_ID
            result = {
                "top1": {"class_id": int(top1_id), "class_name": top1_name, "score": float(top1_cnt / len(votes))},
                "topk": [{
                    "class_id": (CLASS_NAMES.index(name) + 1) if name in CLASS_NAMES else DEFAULT_CLASS_ID,
                    "class_name": name,
                    "score": float(cnt / len(votes))
                } for name, cnt in top],
                "evidence": evidences,
                "meta": {"fps": float(fps), "width": int(w), "height": int(h), "total_frames": int(total)}
            }

        json_path = os.path.join(art_dir, "classification.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        out = {"out_dir": out_dir, "classification_json": json_path, "top1": result["top1"]}
        sample.update(out)
        logger.info(f"Done. classification_json={json_path}")
        return sample
