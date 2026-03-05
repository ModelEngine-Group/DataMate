# -*- coding: utf-8 -*-
import os
import json
import cv2
from ultralytics import YOLO

from .._video_common.io_video import get_video_info
from .._video_common.schema import init_tracks_schema
from .._video_common.paths import make_run_dir
from .._video_common.log import get_logger

def _draw_tracks(frame, objects):
    for obj in objects:
        x1, y1, x2, y2 = map(int, obj["bbox"])
        tid = obj["track_id"]
        score = obj.get("score", 0.0)
        cls_id = obj.get("cls_id", -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        text = f"id={tid} cls={cls_id} {score:.2f}"
        cv2.putText(frame, text, (x1, max(0, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame

class VideoMotTrack:
    """
    多目标追踪算子：
    输入: sample["filePath"], sample["export_path"]
    输出: tracks.json + debug.mp4
    """
    def execute(self, sample: dict, params: dict = None):
        params = params or {}
        video_path = sample["filePath"]
        export_path = sample["export_path"]

        out_dir = make_run_dir(export_path, "video_mot_track")
        logger = get_logger("VideoMotTrack", log_dir=out_dir)

        # 让 ultralytics 配置可写（避免 warning）
        os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(out_dir, ".ultralytics"))
        os.makedirs(os.environ["YOLO_CONFIG_DIR"], exist_ok=True)

        # 默认使用算子包内置权重（离线环境不触发下载）
        default_weight = os.path.join(os.path.dirname(__file__), "weights", "yolov8n.pt")
        yolo_model = params.get("yolo_model", default_weight)
        
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

        debug_path = os.path.join(out_dir, "debug.mp4")
        debug_writer = None
        if save_debug:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            debug_writer = cv2.VideoWriter(debug_path, fourcc, fps, (W, H))

        logger.info(f"Start tracking. video={video_path}, model={yolo_model}, conf={conf}, iou={iou}, classes={classes}")

        model = YOLO(yolo_model)
        results_iter = model.track(
            source=video_path,
            conf=conf,
            iou=iou,
            classes=cls_list,
            tracker=tracker_cfg,
            persist=True,
            verbose=False,
            stream=True,
        )

        for frame_id, r in enumerate(results_iter):
            frame = r.orig_img
            objs = []

            if r.boxes is not None and r.boxes.id is not None:
                xyxy = r.boxes.xyxy.cpu().numpy()
                confs = r.boxes.conf.cpu().numpy()
                clss = r.boxes.cls.cpu().numpy().astype(int)
                tids = r.boxes.id.cpu().numpy().astype(int)

                for box, s, c, tid in zip(xyxy, confs, clss, tids):
                    x1, y1, x2, y2 = box.tolist()
                    objs.append({
                        "track_id": int(tid),
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "score": float(s),
                        "cls_id": int(c),
                    })

            tracks["frames"].append({"frame_id": frame_id, "objects": objs})

            if debug_writer is not None:
                vis = frame.copy()
                vis = _draw_tracks(vis, objs)
                debug_writer.write(vis)

        if debug_writer is not None:
            debug_writer.release()

        json_path = os.path.join(out_dir, "tracks.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(tracks, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. tracks_json={json_path}, debug={debug_path if save_debug else None}")

        # 返回给 runner
        return {
            "out_dir": out_dir,
            "tracks_json": json_path,
            "debug_video": debug_path if save_debug else None,
        }