"""服务：将自动标注（YOLO）结果同步到 Label Studio 作为 predictions。

该服务不负责执行模型推理，只负责：
- 读取本地 annotations JSON（由 runtime/ops/annotation/image_object_detection_bounding_box 产出）；
- 根据 Label Studio 项目的任务列表，将每个文件对应到具体 task；
- 将检测结果转换为 Label Studio 的 prediction 结构并写入。
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Dict, Any, List, Optional

from app.core.logging import get_logger

from ..client import LabelStudioClient

logger = get_logger(__name__)


class PredictionSyncService:
    """将 YOLO 检测结果推送到 Label Studio 的预测服务。"""

    def __init__(self, ls_client: LabelStudioClient) -> None:
        self.ls_client = ls_client

    async def _build_task_index(self, project_id: str) -> Dict[str, int]:
        """为指定项目构建 "文件名 -> task_id" 索引。

        优先使用 data.original_name，其次退回到从 data.image / data.file_path
        中解析出的文件名，保证与 YOLO JSON 中的 annotations["image"] 对得上。
        """

        result = await self.ls_client.get_project_tasks(project_id=project_id, page=None)
        if not result:
            logger.warning("No tasks found for project %s", project_id)
            return {}

        tasks = result.get("tasks", []) or []
        index: Dict[str, int] = {}

        for task in tasks:
            task_id = task.get("id")
            data = task.get("data", {}) or {}
            if task_id is None:
                continue

            # candidate names that may appear in YOLO annotations["image"]
            candidates: List[str] = []

            original_name = data.get("original_name")
            if isinstance(original_name, str) and original_name:
                candidates.append(original_name)

            image_val = data.get("image") or data.get("file_path")
            if isinstance(image_val, str) and image_val:
                basename = os.path.basename(image_val)
                if basename:
                    candidates.append(basename)

            for name in candidates:
                # 后写覆盖前写没关系，同一文件名对应同一个 task 的预期
                index[name] = task_id

        logger.debug(
            "Built task index for project %s with %d entries", project_id, len(index)
        )
        return index

    @staticmethod
    def _build_ls_result_from_detections(
        annotations: Dict[str, Any],
        from_name: str = "label",
        to_name: str = "image",
    ) -> List[Dict[str, Any]]:
        """将 YOLO annotations["detections"] 转为 Label Studio result 列表。"""

        width = float(annotations.get("width") or 0) or 1.0
        height = float(annotations.get("height") or 0) or 1.0
        detections = annotations.get("detections") or []

        results: List[Dict[str, Any]] = []

        for det in detections:
            try:
                label = det.get("label")
                bbox = det.get("bbox_xywh") or det.get("bbox_xyxy")
                if not label or not bbox or len(bbox) < 4:
                    continue

                # 优先使用 xywh，单位像素
                if len(bbox) == 4:
                    x, y, w, h = map(float, bbox)
                else:
                    # 回退：如果给的是 xyxy
                    x1, y1, x2, y2 = map(float, bbox[:4])
                    x, y, w, h = x1, y1, x2 - x1, y2 - y1

                x_pct = max(0.0, min(100.0, x / width * 100.0))
                y_pct = max(0.0, min(100.0, y / height * 100.0))
                w_pct = max(0.0, min(100.0, w / width * 100.0))
                h_pct = max(0.0, min(100.0, h / height * 100.0))

                region_id = uuid.uuid4().hex[:10]

                results.append(
                    {
                        "id": region_id,
                        "type": "rectanglelabels",
                        "value": {
                            "x": x_pct,
                            "y": y_pct,
                            "width": w_pct,
                            "height": h_pct,
                            "rotation": 0,
                            "rectanglelabels": [label],
                        },
                        "origin": "prediction",
                        "to_name": to_name,
                        "from_name": from_name,
                        "image_rotation": 0,
                        "original_width": width,
                        "original_height": height,
                    }
                )
            except Exception as exc:  # 防御性：单条失败不影响其他
                logger.warning("Failed to convert detection to LS result: %s", exc)
                continue

        return results

    async def sync_predictions_from_dir(
        self,
        project_id: str,
        annotations_dir: str,
        *,
        model_version: Optional[str] = None,
        from_name: str = "label",
        to_name: str = "image",
    ) -> int:
        """将某个目录下的 YOLO JSON 同步为给定项目的 predictions。

        返回成功写入 prediction 的任务数。
        """

        if not os.path.isdir(annotations_dir):
            logger.warning("annotations_dir '%s' is not a directory", annotations_dir)
            return 0

        task_index = await self._build_task_index(project_id)
        if not task_index:
            logger.warning(
                "No tasks found when syncing predictions for project %s", project_id
            )
            return 0

        created_count = 0

        for filename in os.listdir(annotations_dir):
            if not filename.lower().endswith(".json"):
                continue

            json_path = os.path.join(annotations_dir, filename)

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    annotations = json.load(f)
            except Exception as exc:
                logger.warning("Failed to load annotations json %s: %s", json_path, exc)
                continue

            image_name = annotations.get("image") or filename.rsplit(".", 1)[0]
            task_id = task_index.get(image_name)
            if task_id is None:
                logger.info(
                    "No matching task for image '%s' in project %s, skip", image_name, project_id
                )
                continue

            result = self._build_ls_result_from_detections(
                annotations, from_name=from_name, to_name=to_name
            )
            if not result:
                logger.info("No detections for %s, skip creating prediction", image_name)
                continue

            mv = model_version
            if mv is None:
                model_size = annotations.get("model_size") or ""
                mv = f"yolov8{model_size}" if model_size else "yolov8"

            prediction = await self.ls_client.create_prediction(
                task_id=task_id,
                result=result,
                model_version=mv,
            )
            if prediction:
                created_count += 1

        logger.info(
            "Synced YOLO predictions from '%s' to project %s, created %d predictions",
            annotations_dir,
            project_id,
            created_count,
        )
        return created_count
