# -*- coding: utf-8 -*-
import json
import os

import cv2

from datamate.core.base_op import Mapper

from .._video_common.io_video import get_video_info
from .._video_common.log import get_logger
from .._video_common.model_paths import resolve_model_path
from .._video_common.params import parse_bool
from .._video_common.paths import ensure_dir, make_run_dir
from .._video_common.schema import init_tracks_schema


def _patch_ultralytics_npu(logger):
    """Patch ultralytics<8.4.22 so select_device() can understand Ascend NPU."""
    try:
        import importlib
        import torch
        import torch_npu  # noqa: F401
        import ultralytics.utils.torch_utils as torch_utils
    except Exception as e:
        logger.warning(f"Ultralytics NPU patch skipped: {e}")
        return False

    if getattr(torch_utils.select_device, "_datamate_npu_patched", False):
        return True

    origin_select_device = torch_utils.select_device

    def patched_select_device(device="", batch=0, newline=False, verbose=True):
        if isinstance(device, torch.device):
            if device.type == "npu":
                idx = 0 if device.index is None else int(device.index)
                if not hasattr(torch, "npu") or not torch.npu.is_available():
                    raise ValueError(f"Requested NPU device {device}, but torch.npu is unavailable")
                torch.npu.set_device(f"npu:{idx}")
                return torch.device(f"npu:{idx}")
            device = str(device)

        device_str = str(device or "").strip().lower().replace(" ", "")
        if device_str.startswith("npu"):
            if not hasattr(torch, "npu") or not torch.npu.is_available():
                raise ValueError(f"Invalid NPU device requested '{device}'. torch_npu is unavailable")
            idx = 0
            if ":" in device_str:
                idx_str = device_str.split(":", 1)[1]
                idx = int(idx_str) if idx_str else 0
            torch.npu.set_device(f"npu:{idx}")
            logger.info(f"Ultralytics select_device patched for Ascend NPU: npu:{idx}")
            return torch.device(f"npu:{idx}")

        return origin_select_device(device=device, batch=batch, newline=newline, verbose=verbose)

    patched_select_device._datamate_npu_patched = True
    torch_utils.select_device = patched_select_device

    for mod_name in (
        "ultralytics.engine.predictor",
        "ultralytics.engine.exporter",
        "ultralytics.engine.trainer",
        "ultralytics.nn.autobackend",
    ):
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "select_device"):
                setattr(mod, "select_device", patched_select_device)
        except Exception:
            pass

    return True


class VideoMotTrack(Mapper):
    """多目标跟踪（YOLO + ByteTrack）。

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.params = dict(kwargs)

    def execute(self, sample: dict, params: dict = None):
        params = params or self.params
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        out_dir = make_run_dir(export_path, "video_mot_track")
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))
        logger = get_logger("VideoMotTrack", log_dir)

        # 避免将 YOLO 配置写入不可写目录。
        os.environ.setdefault("YOLO_CONFIG_DIR", os.path.join(out_dir, "yolo_cfg"))
        os.makedirs(os.environ["YOLO_CONFIG_DIR"], exist_ok=True)

        # 模型仓默认权重。
        yolo_model = resolve_model_path(params, "yolo_model", "yolo/yolov8n.pt")

        conf = float(params.get("conf", 0.3))
        iou = float(params.get("iou", 0.5))
        classes = params.get("classes", None)  # "0,2,3" or None
        tracker_cfg = params.get("tracker_cfg") or os.path.join(
            os.path.dirname(__file__), "configs/bytetrack.yaml"
        )
        save_debug = parse_bool(params.get("save_debug", True), default=True)
        device = str(params.get("device", "") or "").strip()

        cls_list = None
        if classes:
            cls_list = [int(x.strip()) for x in str(classes).split(",") if x.strip() != ""]

        fps, width, height, _ = get_video_info(video_path)
        tracks = init_tracks_schema(video_path, fps, width, height)

        debug_path = os.path.join(art_dir, "debug.mp4")
        debug_writer = None
        if save_debug:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            debug_writer = cv2.VideoWriter(debug_path, fourcc, fps, (width, height))

        logger.info(
            f"Start tracking. video={video_path}, model={yolo_model}, conf={conf}, iou={iou}, classes={classes}"
        )
        if not os.path.exists(yolo_model):
            raise RuntimeError(f"YOLO weight not found: {yolo_model}. Please download to model repo path.")

        try:
            patch_ok = _patch_ultralytics_npu(logger)
            import ultralytics
            from ultralytics import YOLO

            logger.info(f"Ultralytics version: {getattr(ultralytics, '__version__', 'unknown')}, patch_ok={patch_ok}")
        except Exception as e:
            raise RuntimeError(
                "ultralytics is not installed. Please rebuild the runtime image with runtime/ops dependencies."
            ) from e

        accelerator = str(getattr(self, "accelerator", "cpu") or "cpu").strip().lower()
        npu_available = False
        npu_err = None
        current_device = 0
        if not device:
            try:
                import torch_npu

                npu_available = bool(torch_npu.npu.is_available())
                if npu_available:
                    current_device = torch_npu.npu.current_device()
            except Exception as e:
                npu_err = e

            if accelerator == "npu" and npu_available:
                device = f"npu:{current_device}"
            elif npu_available:
                logger.warning(
                    f"accelerator={accelerator} but torch_npu is available, auto switching to npu:{current_device}"
                )
                device = f"npu:{current_device}"
            else:
                if npu_err is not None:
                    logger.warning(f"torch_npu probe failed, fallback to cpu. err={npu_err}")
                device = "cpu"

        logger.info(f"Tracking device resolved to: {device} (accelerator={accelerator}, npu_available={npu_available})")
        model = YOLO(yolo_model)
        if str(device).startswith("npu"):
            try:
                if hasattr(model, "model") and hasattr(model.model, "to"):
                    model.model.to(device)
                    logger.info(f"YOLO model moved to {device}")
            except Exception as e:
                logger.warning(f"Failed to move YOLO model to {device} before track(): {e}")

        track_kwargs = dict(
            source=video_path,
            conf=conf,
            iou=iou,
            classes=cls_list,
            tracker=tracker_cfg,
            stream=True,
            verbose=False,
        )
        if device:
            track_kwargs["device"] = device
        results_iter = model.track(**track_kwargs)

        frame_idx = 0
        for result in results_iter:
            frame = result.orig_img
            objects = []
            if result.boxes is not None and result.boxes.id is not None:
                ids = result.boxes.id.cpu().numpy().tolist()
                xyxy = result.boxes.xyxy.cpu().numpy().tolist()
                confs = result.boxes.conf.cpu().numpy().tolist()
                classes_out = result.boxes.cls.cpu().numpy().tolist()
                for tid, bbox, score, cls_id in zip(ids, xyxy, confs, classes_out):
                    x1, y1, x2, y2 = bbox
                    objects.append(
                        {
                            "track_id": int(tid),
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "score": float(score),
                            "cls_id": int(cls_id),
                        }
                    )
                    if debug_writer is not None:
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        cv2.putText(
                            frame,
                            f"id={int(tid)}",
                            (int(x1), int(y1) - 5),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )
            tracks["frames"].append({"frame_idx": frame_idx, "objects": objects})

            if debug_writer is not None:
                debug_writer.write(frame)
            frame_idx += 1

        if debug_writer is not None:
            debug_writer.release()

        tracks_path = os.path.join(art_dir, "tracks.json")
        with open(tracks_path, "w", encoding="utf-8") as fh:
            json.dump(tracks, fh, ensure_ascii=False, indent=2)

        logger.info(f"Done. tracks_json={tracks_path}")
        out = {"out_dir": out_dir, "tracks_json": tracks_path}
        if save_debug:
            out["debug_mp4"] = debug_path
        sample.update(out)
        return sample
