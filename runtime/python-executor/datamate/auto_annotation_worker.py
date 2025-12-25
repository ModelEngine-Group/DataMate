# -*- coding: utf-8 -*-
"""Simple background worker for auto-annotation tasks.

This module runs inside the datamate-runtime container (operator_runtime service).
It polls `t_dm_auto_annotation_tasks` for pending tasks and performs YOLO
inference using the ImageObjectDetectionBoundingBox operator, updating
progress back to the same table so that the datamate-python backend and
frontend can display real-time status.

设计目标（最小可用版本）:
- 单实例 worker，串行处理 `pending` 状态的任务。
- 对指定数据集下的所有已完成文件逐张执行目标检测。
- 按已处理图片数更新 `processed_images`、`progress`、`detected_objects`、`status` 等字段。
- 失败时将任务标记为 `failed` 并记录 `error_message`。

注意:
- 为了保持简单，目前不处理 "running" 状态的恢复逻辑；容器重启时，
  已处于 running 的任务不会被重新拉起，需要后续扩展。
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import text

from datamate.sql_manager.sql_manager import SQLManager

try:
    # 在 runtime 容器中，算子作为 datamate 包的一部分安装，使用 datamate.ops 前缀导入
    from datamate.ops.annotation.image_object_detection_bounding_box.process import (
        ImageObjectDetectionBoundingBox,
    )
except Exception as e:  # pragma: no cover - 导入失败时仅记录日志，避免整体崩溃
    logger.error(
        "Failed to import ImageObjectDetectionBoundingBox operator via datamate.ops: {}",
        e,
    )
    ImageObjectDetectionBoundingBox = None  # type: ignore


POLL_INTERVAL_SECONDS = float(os.getenv("AUTO_ANNOTATION_POLL_INTERVAL", "5"))

# 结果输出基础目录默认不再使用单独的 auto-annotations 目录，
# 而是优先写入原始数据集的 path 目录下，便于在同一数据集中直接查看。
# 仅当无法从 t_dm_datasets 中查询到 path 时，才退回到该根目录下。
DEFAULT_OUTPUT_ROOT = os.getenv(
    "AUTO_ANNOTATION_OUTPUT_ROOT", "/dataset"
)


def _fetch_pending_task() -> Optional[Dict[str, Any]]:
    """从 t_dm_auto_annotation_tasks 中取出一个 pending 任务。

    为简化实现，这里不做显式行锁控制，假设只有单个 runtime 实例在轮询。
    """

    sql = text(
        """
        SELECT id, name, dataset_id, dataset_name, config, file_ids, status,
               total_images, processed_images, detected_objects, output_path
        FROM t_dm_auto_annotation_tasks
        WHERE status = 'pending' AND deleted_at IS NULL
        ORDER BY created_at ASC
        LIMIT 1
        """
    )

    with SQLManager.create_connect() as conn:
        result = conn.execute(sql).fetchone()
        if not result:
            return None
        row = dict(result._mapping)  # type: ignore[attr-defined]

    # config 与 file_ids 存储为 JSON 字符串，这里做一次解析
    try:
        row["config"] = json.loads(row["config"]) if row.get("config") else {}
    except Exception:
        row["config"] = {}

    try:
        raw_ids = row.get("file_ids")
        if not raw_ids:
            row["file_ids"] = None
        elif isinstance(raw_ids, str):
            row["file_ids"] = json.loads(raw_ids)
        else:
            row["file_ids"] = raw_ids
    except Exception:
        row["file_ids"] = None
    return row


def _update_task_status(
    task_id: str,
    *,
    status: str,
    progress: Optional[int] = None,
    processed_images: Optional[int] = None,
    detected_objects: Optional[int] = None,
    total_images: Optional[int] = None,
    output_path: Optional[str] = None,
    error_message: Optional[str] = None,
    completed: bool = False,
) -> None:
    """更新任务的状态和统计字段。"""

    fields: List[str] = ["status = :status", "updated_at = :updated_at"]
    params: Dict[str, Any] = {
        "task_id": task_id,
        "status": status,
        "updated_at": datetime.now(),
    }

    if progress is not None:
        fields.append("progress = :progress")
        params["progress"] = int(progress)
    if processed_images is not None:
        fields.append("processed_images = :processed_images")
        params["processed_images"] = int(processed_images)
    if detected_objects is not None:
        fields.append("detected_objects = :detected_objects")
        params["detected_objects"] = int(detected_objects)
    if total_images is not None:
        fields.append("total_images = :total_images")
        params["total_images"] = int(total_images)
    if output_path is not None:
        fields.append("output_path = :output_path")
        params["output_path"] = output_path
    if error_message is not None:
        fields.append("error_message = :error_message")
        params["error_message"] = error_message[:2000]
    if completed:
        fields.append("completed_at = :completed_at")
        params["completed_at"] = datetime.now()

    sql = text(
        f"""
        UPDATE t_dm_auto_annotation_tasks
        SET {', '.join(fields)}
        WHERE id = :task_id
        """
    )

    with SQLManager.create_connect() as conn:
        conn.execute(sql, params)


def _load_dataset_files(dataset_id: str) -> List[Tuple[str, str, str]]:
    """加载指定数据集下的所有已完成文件。

    返回 (file_id, file_path, file_name) 列表。
    """

    # 数据管理模块中，t_dm_dataset_files 的正常状态为 ACTIVE，
    # 不存在 deleted_at 字段，这里仅按 dataset_id + ACTIVE 过滤。
    sql = text(
        """
        SELECT id, file_path, file_name
        FROM t_dm_dataset_files
        WHERE dataset_id = :dataset_id
          AND status = 'ACTIVE'
        ORDER BY created_at ASC
        """
    )

    with SQLManager.create_connect() as conn:
        rows = conn.execute(sql, {"dataset_id": dataset_id}).fetchall()
        return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]


def _load_files_by_ids(file_ids: List[str]) -> List[Tuple[str, str, str]]:
    """根据文件ID列表加载文件记录，支持跨多个数据集。

    返回 (file_id, file_path, file_name) 列表。
    """

    if not file_ids:
        return []

    # 使用参数化方式构造 IN 子句，避免 SQL 注入
    placeholders = ", ".join(f":id{i}" for i in range(len(file_ids)))
    sql = text(
        f"""
        SELECT id, file_path, file_name
        FROM t_dm_dataset_files
        WHERE id IN ({placeholders})
          AND status = 'ACTIVE'
        ORDER BY created_at ASC
        """
    )
    params = {f"id{i}": str(fid) for i, fid in enumerate(file_ids)}

    with SQLManager.create_connect() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [(str(r[0]), str(r[1]), str(r[2])) for r in rows]


def _ensure_output_dir(output_dir: str) -> str:
    """确保输出目录及其 images/、annotations/ 子目录存在。"""

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "annotations"), exist_ok=True)
    return output_dir


def _create_output_dataset(
    source_dataset_id: str,
    source_dataset_name: str,
    output_dataset_name: str,
) -> Tuple[str, str]:
    """为自动标注结果创建一个新的数据集并返回 (dataset_id, path)。

    - 新数据集使用 IMAGE 类型；
    - 路径遵循后端约定：{base_path}/{dataset_id}，其中 base_path 与 DEFAULT_OUTPUT_ROOT 对齐；
    - 不依赖前端/后端的额外服务，直接写入 t_dm_datasets 表。
    """

    new_dataset_id = str(uuid.uuid4())
    dataset_base_path = DEFAULT_OUTPUT_ROOT.rstrip("/") or "/dataset"
    output_dir = os.path.join(dataset_base_path, new_dataset_id)

    description = (
        f"Auto annotations for dataset {source_dataset_name or source_dataset_id}"[:255]
    )

    sql = text(
        """
        INSERT INTO t_dm_datasets (id, name, description, dataset_type, path, status)
        VALUES (:id, :name, :description, :dataset_type, :path, :status)
        """
    )
    params = {
        "id": new_dataset_id,
        "name": output_dataset_name,
        "description": description,
        "dataset_type": "IMAGE",
        "path": output_dir,
        "status": "ACTIVE",
    }

    with SQLManager.create_connect() as conn:
        conn.execute(sql, params)

    return new_dataset_id, output_dir


def _register_output_dataset(
    task_id: str,
    output_dataset_id: str,
    output_dir: str,
    output_dataset_name: str,
    total_images: int,
) -> None:
    """将自动标注结果注册到**新建的数据集**中。

    - 假定目标数据集记录已存在（由 _create_output_dataset 创建）；
    - 在 t_dm_dataset_files 中为输出目录下的 images/ 和 annotations/ 文件
      创建文件记录，dataset_id 使用新数据集 ID；
    - 同时累加该数据集的 file_count 与 size_bytes。

    失败不会影响任务本身，仅记录日志。
    """

    images_dir = os.path.join(output_dir, "images")
    if not os.path.isdir(images_dir):
        logger.warning(
            "Auto-annotation images directory not found for task {}: {}",
            task_id,
            images_dir,
        )
        return

    image_files: List[Tuple[str, str, int]] = []
    annotation_files: List[Tuple[str, str, int]] = []
    total_size = 0

    # 收集标注后的图片
    for file_name in sorted(os.listdir(images_dir)):
        file_path = os.path.join(images_dir, file_name)
        if not os.path.isfile(file_path):
            continue
        try:
            file_size = os.path.getsize(file_path)
        except OSError:
            file_size = 0
        image_files.append((file_name, file_path, int(file_size)))
        total_size += int(file_size)

    # 收集 JSON 标注
    annotations_dir = os.path.join(output_dir, "annotations")
    if os.path.isdir(annotations_dir):
        for file_name in sorted(os.listdir(annotations_dir)):
            file_path = os.path.join(annotations_dir, file_name)
            if not os.path.isfile(file_path):
                continue
            try:
                file_size = os.path.getsize(file_path)
            except OSError:
                file_size = 0
            annotation_files.append((file_name, file_path, int(file_size)))
            total_size += int(file_size)

    if not image_files:
        logger.warning(
            "No image files found in auto-annotation output for task {}: {}",
            task_id,
            images_dir,
        )
        return

    # 准备 SQL：向目标数据集追加文件记录，并更新统计字段
    insert_file_sql = text(
        """
        INSERT INTO t_dm_dataset_files (
            id, dataset_id, file_name, file_path, file_type, file_size, status
        ) VALUES (
            :id, :dataset_id, :file_name, :file_path, :file_type, :file_size, :status
        )
        """
    )
    update_dataset_stat_sql = text(
        """
        UPDATE t_dm_datasets
        SET file_count = COALESCE(file_count, 0) + :add_count,
            size_bytes = COALESCE(size_bytes, 0) + :add_size
        WHERE id = :dataset_id
        """
    )

    with SQLManager.create_connect() as conn:
        # 为目标数据集追加文件记录：先图片，再 JSON 标注
        added_count = 0

        for file_name, file_path, file_size in image_files:
            ext = os.path.splitext(file_name)[1].lstrip(".").upper() or None
            conn.execute(
                insert_file_sql,
                {
                    "id": str(uuid.uuid4()),
                    "dataset_id": output_dataset_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_type": ext,
                    "file_size": int(file_size),
                    "status": "ACTIVE",
                },
            )
            added_count += 1

        for file_name, file_path, file_size in annotation_files:
            ext = os.path.splitext(file_name)[1].lstrip(".").upper() or None
            conn.execute(
                insert_file_sql,
                {
                    "id": str(uuid.uuid4()),
                    "dataset_id": output_dataset_id,
                    "file_name": file_name,
                    "file_path": file_path,
                    "file_type": ext,
                    "file_size": int(file_size),
                    "status": "ACTIVE",
                },
            )
            added_count += 1

        # 更新目标数据集的统计字段
        if added_count > 0:
            conn.execute(
                update_dataset_stat_sql,
                {
                    "dataset_id": output_dataset_id,
                    "add_count": added_count,
                    "add_size": int(total_size),
                },
            )

    logger.info(
        "Registered auto-annotation output into dataset: dataset_id={}, name={}, added_files={}, added_size_bytes={}, task_id={}, output_dir={}",
        output_dataset_id,
        output_dataset_name,
        len(image_files) + len(annotation_files),
        total_size,
        task_id,
        output_dir,
    )


def _process_single_task(task: Dict[str, Any]) -> None:
    """执行单个自动标注任务。"""

    if ImageObjectDetectionBoundingBox is None:
        logger.error(
            "YOLO operator not available (import failed earlier), skip auto-annotation task: {}",
            task["id"],
        )
        _update_task_status(
            task["id"],
            status="failed",
            error_message="YOLO operator not available in runtime container",
        )
        return

    task_id = str(task["id"])
    dataset_id = str(task["dataset_id"])
    task_name = str(task.get("name") or "")
    source_dataset_name = str(task.get("dataset_name") or "")
    cfg: Dict[str, Any] = task.get("config") or {}
    selected_file_ids: Optional[List[str]] = task.get("file_ids") or None

    model_size = cfg.get("modelSize", "l")
    conf_threshold = float(cfg.get("confThreshold", 0.7))
    target_classes = cfg.get("targetClasses", []) or []
    output_dataset_name = cfg.get("outputDatasetName")

    # 如果前端/配置未显式提供输出数据集名称，则自动生成一个易于识别的名称
    if not output_dataset_name:
        base_name = source_dataset_name or task_name or f"dataset-{dataset_id[:8]}"
        output_dataset_name = f"{base_name}_auto_{task_id[:8]}"

    logger.info(
        "Start processing auto-annotation task: id={}, dataset_id={}, model_size={}, conf_threshold={}, target_classes={}, output_dataset_name={}",
        task_id,
        dataset_id,
        model_size,
        conf_threshold,
        target_classes,
        output_dataset_name,
    )

    # 标记为 running
    _update_task_status(task_id, status="running", progress=0)

    # 加载待处理文件：
    # - 如果未提供 file_ids，则处理该数据集下的全部文件；
    # - 如果提供了 file_ids，则按 ID 跨数据集精确加载，支持多数据集混合。
    if selected_file_ids:
            all_files = _load_files_by_ids(selected_file_ids)
    else:
            all_files = _load_dataset_files(dataset_id)

    files = [(path, name) for _, path, name in all_files]

    total_images = len(files)
    if total_images == 0:
        logger.warning("No files found for dataset {} when running auto-annotation task {}", dataset_id, task_id)
        _update_task_status(
            task_id,
            status="completed",
            progress=100,
            total_images=0,
            processed_images=0,
            detected_objects=0,
            completed=True,
            output_path=None,
        )
        return

    # 为本次任务创建一个新的“输出数据集”，并以其路径作为 YOLO 输出目录
    output_dataset_id, output_dir = _create_output_dataset(
            source_dataset_id=dataset_id,
            source_dataset_name=source_dataset_name,
            output_dataset_name=output_dataset_name,
    )
    output_dir = _ensure_output_dir(output_dir)

    # 初始化检测算子
    try:
        detector = ImageObjectDetectionBoundingBox(
            modelSize=model_size,
            confThreshold=conf_threshold,
            targetClasses=target_classes,
            outputDir=output_dir,
        )
    except Exception as e:
        logger.error("Failed to init YOLO detector for task {}: {}", task_id, e)
        _update_task_status(
            task_id,
            status="failed",
            total_images=total_images,
            processed_images=0,
            detected_objects=0,
            error_message=f"Init YOLO detector failed: {e}",
        )
        return

    processed = 0
    detected_total = 0

    for file_path, file_name in files:
        try:
            sample = {
                "image": file_path,
                "filename": file_name,
            }
            result = detector.execute(sample)

            annotations = (result or {}).get("annotations", {})
            detections = annotations.get("detections", [])
            detected_total += len(detections)
            processed += 1

            # 计算进度
            progress = int(processed * 100 / total_images) if total_images > 0 else 100

            _update_task_status(
                task_id,
                status="running",
                progress=progress,
                processed_images=processed,
                detected_objects=detected_total,
                total_images=total_images,
                output_path=output_dir,
            )
        except Exception as e:
            logger.error(
                "Failed to process image for task {}: file_path={}, error={}",
                task_id,
                file_path,
                e,
            )
            # 不中断整个任务，继续处理后续图片
            continue

    # 任务完成
    _update_task_status(
        task_id,
        status="completed",
        progress=100,
        processed_images=processed,
        detected_objects=detected_total,
        total_images=total_images,
        output_path=output_dir,
        completed=True,
    )

    logger.info(
        "Completed auto-annotation task: id={}, total_images={}, processed={}, detected_objects={}, output_path={}",
        task_id,
        total_images,
        processed,
        detected_total,
        output_dir,
    )

    # 如果配置了输出数据集名称，则尝试将结果注册为新的数据集
    if output_dataset_name and output_dataset_id:
        try:
            _register_output_dataset(
                task_id=task_id,
                        output_dataset_id=output_dataset_id,
                output_dir=output_dir,
                output_dataset_name=output_dataset_name,
                total_images=total_images,
            )
        except Exception as e:  # pragma: no cover - 防御性日志
            logger.error(
                "Failed to register auto-annotation output as dataset for task {}: {}",
                task_id,
                e,
            )


def _worker_loop() -> None:
    """Worker 主循环，在独立线程中运行。"""

    logger.info(
        "Auto-annotation worker started with poll interval {} seconds, output root {}",
        POLL_INTERVAL_SECONDS,
        DEFAULT_OUTPUT_ROOT,
    )

    while True:
        try:
            task = _fetch_pending_task()
            if not task:
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            _process_single_task(task)
        except Exception as e:  # pragma: no cover - 防御性日志
            logger.error("Auto-annotation worker loop error: {}", e)
            # 避免死循环高频报错
            time.sleep(POLL_INTERVAL_SECONDS)


def start_auto_annotation_worker() -> None:
    """在后台线程中启动自动标注 worker。

    该函数可在 operator_runtime 应用启动时调用。
    """

    thread = threading.Thread(target=_worker_loop, name="auto-annotation-worker", daemon=True)
    thread.start()
    logger.info("Auto-annotation worker thread started: {}", thread.name)
