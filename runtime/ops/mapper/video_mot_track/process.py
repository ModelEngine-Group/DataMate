# -*- coding: utf-8 -*-
import os
import json
import cv2
import shutil

from ultralytics import YOLO

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger
from .._video_common.io_video import get_video_info
from .._video_common.schema import init_tracks_schema
from .._video_common.model_paths import resolve_model_path


class VideoMotTrack:
    """多目标跟踪（YOLO + ByteTrack）

    权重策略（模型仓）：
      DATAMATE_MODEL_ROOT=/mnt/models
      默认权重：/mnt/models/yolo/yolov8n.pt
    params:
      - model_root: 可选，覆盖 DATAMATE_MODEL_ROOT
      - yolo_model: 可选，权重路径（相对/绝对均可）
      - conf: default 0.3
      - iou: default 0.5
      - classes: "0,2,3" or None
      - tracker_cfg: bytetrack yaml 路径（默认算子 configs/bytetrack.yaml）
      - save_debug: default True
    outputs:
      - tracks.json
      - debug.mp4 (optional)
    """

    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_mot_track")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        logger = get_logger("VideoMotTrack", log_dir)

        # YOLO config dir（避免写到不可写目录）
        os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(out_dir, "yolo_cfg"))
        os.makedirs(os.environ["YOLO_CONFIG_DIR"], exist_ok=True)

        # ✅ 模型仓默认权重
        yolo_model = resolve_model_path(params, "yolo_model", "yolo/yolov8n.pt")

        conf = float(params.get("conf", 0.3))
        iou = float(params.get("iou", 0.5))
        classes = params.get("classes", None)  # "0,2,3" or None
        tracker_cfg = params.get("tracker_cfg", os.path.join(os.path.dirname(__file__), "configs/bytetrack.yaml"))
        save_debug = bool(params.get("save_debug", True))

        cls_list = None
        if classes:
            cls_list = [int(x.strip()) for x in str(classes).split(",") if x.strip() != ""]

        fps, W, H, _ = get_video_info(video_path)
        tracks = init_tracks_schema(video_path, fps, W, H)

        debug_path = os.path.join(art_dir, "debug.mp4")
        debug_writer = None
        if save_debug:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            debug_writer = cv2.VideoWriter(debug_path, fourcc, fps, (W, H))

        logger.info(f"Start tracking. video={video_path}, model={yolo_model}, conf={conf}, iou={iou}, classes={classes}")
        if not os.path.exists(yolo_model):
            raise RuntimeError(f"YOLO weight not found: {yolo_model}. Please download to model repo path.")

        model = YOLO(yolo_model)
        results_iter = model.track(
            source=video_path,
            conf=conf,
            iou=iou,
            classes=cls_list,
            tracker=tracker_cfg,
            stream=True,
            verbose=False,
        )

        frame_idx = 0
        for r in results_iter:
            frame = r.orig_img
            objs = []
            if r.boxes is not None and r.boxes.id is not None:
                ids = r.boxes.id.cpu().numpy().tolist()
                xyxy = r.boxes.xyxy.cpu().numpy().tolist()
                confs = r.boxes.conf.cpu().numpy().tolist()
                clss = r.boxes.cls.cpu().numpy().tolist()
                for tid, bb, sc, cc in zip(ids, xyxy, confs, clss):
                    x1, y1, x2, y2 = bb
                    objs.append({
                        "track_id": int(tid),
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "score": float(sc),
                        "cls_id": int(cc),
                    })
                    if debug_writer is not None:
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
                        cv2.putText(frame, f"id={int(tid)}", (int(x1), int(y1)-5),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            tracks["frames"].append({"frame_idx": frame_idx, "objects": objs})

            if debug_writer is not None:
                debug_writer.write(frame)
            frame_idx += 1

        if debug_writer is not None:
            debug_writer.release()

        tracks_path = os.path.join(art_dir, "tracks.json")
        with open(tracks_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. tracks_json={tracks_path}")
        out = {"out_dir": out_dir, "tracks_json": tracks_path}
        if save_debug:
            out["debug_mp4"] = debug_path
        return out