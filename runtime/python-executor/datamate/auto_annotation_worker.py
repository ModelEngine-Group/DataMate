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
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from loguru import logger
from sqlalchemy import text

from datamate.sql_manager.sql_manager import SQLManager

# 尝试多种导入路径，适配不同的打包/安装方式
ImageObjectDetectionBoundingBox = None  # type: ignore
try:
    # 优先使用 datamate.ops 路径（源码 COPY 到 /opt/runtime/datamate/ops 情况）
    from datamate.ops.annotation.image_object_detection_bounding_box.process import (  # type: ignore
        ImageObjectDetectionBoundingBox,
    )
    logger.info(
        "Imported ImageObjectDetectionBoundingBox from datamate.ops.annotation.image_object_detection_bounding_box",
    )
except Exception as e1:  # pragma: no cover - 导入失败时仅记录日志，避免整体崩溃
    logger.error(
        "Failed to import ImageObjectDetectionBoundingBox via datamate.ops: {}",
        e1,
    )
    try:
        # 兼容顶层 ops 包安装的情况（通过 ops.pth 暴露）
        from ops.annotation.image_object_detection_bounding_box.process import (  # type: ignore
            ImageObjectDetectionBoundingBox,
        )
        logger.info(
            "Imported ImageObjectDetectionBoundingBox from top-level ops.annotation.image_object_detection_bounding_box",
        )
    except Exception as e2:
        logger.error(
            "Failed to import ImageObjectDetectionBoundingBox via top-level ops package: {}",
            e2,
        )
        ImageObjectDetectionBoundingBox = None


# 进一步兜底：直接从本地 runtime/ops 目录加载算子（开发环境常用场景）
if ImageObjectDetectionBoundingBox is None:
    try:
        project_root = Path(__file__).resolve().parents[2]
        ops_root = project_root / "ops"
        if ops_root.is_dir():
            # 确保 ops 的父目录在 sys.path 中，这样可以按 "ops.xxx" 导入
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from ops.annotation.image_object_detection_bounding_box.process import (  # type: ignore
                ImageObjectDetectionBoundingBox,
            )

            logger.info(
                "Imported ImageObjectDetectionBoundingBox from local runtime/ops.annotation.image_object_detection_bounding_box",
            )
        else:
            logger.warning(
                "Local runtime/ops directory not found when trying to import ImageObjectDetectionBoundingBox: {}",
                ops_root,
            )
    except Exception as e3:  # pragma: no cover - 兜底失败仅记录日志
        logger.error(
            "Failed to import ImageObjectDetectionBoundingBox from local runtime/ops: {}",
            e3,
        )
        ImageObjectDetectionBoundingBox = None


POLL_INTERVAL_SECONDS = float(os.getenv("AUTO_ANNOTATION_POLL_INTERVAL", "5"))

DEFAULT_OUTPUT_ROOT = os.getenv(
    "AUTO_ANNOTATION_OUTPUT_ROOT", "/dataset"
)


def _fetch_pending_task() -> Optional[Dict[str, Any]]:
    """从 t_dm_auto_annotation_tasks 中取出一个 pending 任务。"""

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

    # 兼容 config 字段为 JSONB（dict）或 text（str）的两种情况
    raw_cfg = row.get("config")
    if isinstance(raw_cfg, (dict, list)):
        row["config"] = raw_cfg
    elif isinstance(raw_cfg, str) and raw_cfg.strip():
        try:
            row["config"] = json.loads(raw_cfg)
        except Exception:
            row["config"] = {}
    else:
        row["config"] = {}

    # file_ids 同样可能是 JSONB 或 text
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
    """加载指定数据集下的所有已激活文件。

    不再根据 tags 是否为空进行过滤，避免影响后续新任务或重复任务的执行。
    """

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
    """根据文件ID列表加载文件记录，支持跨多个数据集。"""

    if not file_ids:
        return []

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


def _build_file_tags_from_detections(detections: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """根据检测结果构建 FileTag JSON 结构。

    tags 字段在 DM 服务中被当作 List[FileTag] 解析，结构需与
    backend `FileTag`/runtime `DatasetFileTag` 保持兼容：

    [{
        "id": "...",               # 可选
        "type": "labels",         # 类型键
        "from_name": "auto_annotation",  # 来源
        "values": {"labels": ["Person", "Car"]}
    }]

    重复类别只保留一个。
    """

    if not detections:
        return None

    label_set: Set[str] = set()
    for det in detections:
        label = det.get("label")
        if isinstance(label, str) and label:
            label_set.add(label)

    if not label_set:
        return None

    # 排序以保证结果稳定
    labels = sorted(label_set)
    return [
        {
            "id": None,
            "type": "labels",
            "from_name": "auto_annotation",
            "values": {"labels": labels},
        }
    ]


def _update_dataset_file_tags(file_id: str, tags: List[Dict[str, Any]]) -> None:
    """将标签写入 t_dm_dataset_files.tags 并更新 tags_updated_at。"""

    if not file_id:
        return

    try:
        now = datetime.utcnow()
        sql = text(
            """
            UPDATE t_dm_dataset_files
            SET tags = :tags,
                tags_updated_at = :tags_updated_at
            WHERE id = :file_id
            """
        )
        params = {
            "file_id": file_id,
            "tags": json.dumps(tags, ensure_ascii=False),
            "tags_updated_at": now,
        }
        with SQLManager.create_connect() as conn:
            conn.execute(sql, params)
    except Exception as e:  # pragma: no cover - 防御性日志
        logger.error(
            "Failed to update tags for dataset file {}: {}",
            file_id,
            e,
        )


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
    """为自动标注结果创建一个新的数据集并返回 (dataset_id, path)。"""

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
    *,
    tags_by_filename: Optional[Dict[str, List[Dict[str, Any]]]] = None,
) -> None:
    """将自动标注结果注册到数据集。

    如果多次为同一自动标注任务重复运行，将复用同一个输出数据集，并避免对
    同一 dataset_id + file_name 插入重复记录，只为新文件追加记录。
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

    insert_file_sql = text(
        """
        INSERT INTO t_dm_dataset_files (
            id, dataset_id, file_name, file_path, file_type, file_size, status, tags, tags_updated_at
        ) VALUES (
            :id, :dataset_id, :file_name, :file_path, :file_type, :file_size, :status, :tags, :tags_updated_at
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
        added_count = 0

        # 预先查询已存在的文件名，避免重复插入
        existing_names_sql = text(
            """
            SELECT file_name FROM t_dm_dataset_files WHERE dataset_id = :dataset_id
            """
        )
        rows = conn.execute(existing_names_sql, {"dataset_id": output_dataset_id}).fetchall()
        existing_names = {str(r[0]) for r in rows}

        for file_name, file_path, file_size in image_files:
            if file_name in existing_names:
                continue
            ext = os.path.splitext(file_name)[1].lstrip(".").upper() or None
            file_tags = None
            if tags_by_filename:
                file_tags = tags_by_filename.get(file_name)
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
                    "tags": json.dumps(file_tags, ensure_ascii=False) if file_tags else None,
                    "tags_updated_at": datetime.utcnow() if file_tags else None,
                },
            )
            added_count += 1
            existing_names.add(file_name)

        for file_name, file_path, file_size in annotation_files:
            if file_name in existing_names:
                continue
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
                    "tags": None,
                    "tags_updated_at": None,
                },
            )
            added_count += 1
            existing_names.add(file_name)

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

    # 优先使用前端传入的输出数据集名称；若未提供，则使用“源数据集名称+自动标注任务”
    # 兼容历史/不同风格的字段名（如 output_dataset_name）
    output_dataset_name = (
        cfg.get("outputDatasetName")
        or cfg.get("output_dataset_name")
        or task.get("outputDatasetName")
        or task.get("output_dataset_name")
    )
    if isinstance(output_dataset_name, str):
        output_dataset_name = output_dataset_name.strip()

    if not output_dataset_name:
        base_name = source_dataset_name or task_name or f"dataset-{dataset_id[:8]}"
        # 默认规则：源数据集名称 + "自动标注任务"
        output_dataset_name = f"{base_name}自动标注任务"

    logger.info(
        "Start processing auto-annotation task: id={}, dataset_id={}, model_size={}, conf_threshold={}, target_classes={}, output_dataset_name={}",
        task_id,
        dataset_id,
        model_size,
        conf_threshold,
        target_classes,
        output_dataset_name,
    )

    _update_task_status(task_id, status="running", progress=0)

    if selected_file_ids:
        all_files = _load_files_by_ids(selected_file_ids)
    else:
        all_files = _load_dataset_files(dataset_id)

    # 优先复用任务已有的输出目录和对应数据集，避免重复创建结果数据集
    existing_output_path = (task.get("output_path") or "").strip() or None
    output_dataset_id: Optional[str] = None
    output_dir: Optional[str] = None

    if existing_output_path:
        try:
            # 确保目录存在
            output_dir = _ensure_output_dir(existing_output_path)

            # 根据路径查找已存在的数据集记录
            find_dataset_sql = text(
                """
                SELECT id FROM t_dm_datasets
                WHERE path = :path
                ORDER BY created_at DESC
                LIMIT 1
                """
            )
            with SQLManager.create_connect() as conn:
                row = conn.execute(find_dataset_sql, {"path": output_dir}).fetchone()
            if row:
                output_dataset_id = str(row[0])
                logger.info(
                    "Reuse existing output dataset for auto-annotation task: task_id={}, dataset_id={}, path={}",
                    task_id,
                    output_dataset_id,
                    output_dir,
                )
        except Exception as e:
            logger.error(
                "Failed to reuse existing output dataset for task {}: {}",
                task_id,
                e,
            )

    # 如果没有可复用的数据集，则创建新的结果数据集
    if not output_dataset_id or not output_dir:
        output_dataset_id, new_output_dir = _create_output_dataset(
            source_dataset_id=dataset_id,
            source_dataset_name=source_dataset_name,
            output_dataset_name=output_dataset_name,
        )
        output_dir = _ensure_output_dir(new_output_dir)

    # 仅对“新选的数据”执行自动标注：
    # 已经在输出目录 images/ 中存在对应文件名的，认为该任务已跑过，不再重复标注
    existing_image_names: Set[str] = set()
    images_dir = os.path.join(output_dir, "images")
    if os.path.isdir(images_dir):
        try:
            for name in os.listdir(images_dir):
                if not os.path.isfile(os.path.join(images_dir, name)):
                    continue
                existing_image_names.add(name)
        except Exception as e:
            logger.error(
                "Failed to list existing images for auto-annotation task {}: {}",
                task_id,
                e,
            )

    # all_files: List[(file_id, file_path, file_name)]
    files = [
        (file_id, file_path, file_name)
        for file_id, file_path, file_name in all_files
        if os.path.basename(file_path) not in existing_image_names
    ]

    total_images = len(files)
    if total_images == 0:
        logger.info(
            "No new files to process for auto-annotation task {}, reuse existing output at {}",
            task_id,
            output_dir,
        )
        _update_task_status(
            task_id,
            status="completed",
            progress=100,
            total_images=0,
            processed_images=0,
            detected_objects=0,
            completed=True,
            output_path=output_dir,
        )
        return

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

    # 记录：文件名 -> FileTag JSON，用于给新输出数据集的文件打标签
    tags_by_filename: Dict[str, List[Dict[str, Any]]] = {}

    for file_id, file_path, file_name in files:
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

            # 基于检测结果生成标签（按类别去重），并写回源数据集文件
            file_tags = _build_file_tags_from_detections(detections)
            if file_tags:
                try:
                    _update_dataset_file_tags(file_id, file_tags)
                    # 使用源文件名作为 key，供输出数据集复用
                    base_name = os.path.basename(file_path)
                    tags_by_filename[base_name] = file_tags
                except Exception as e:
                    logger.error(
                        "Failed to persist tags for file {} in dataset {}: {}",
                        file_id,
                        dataset_id,
                        e,
                    )

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
            continue

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

    if output_dataset_name and output_dataset_id:
        try:
            _register_output_dataset(
                task_id=task_id,
                output_dataset_id=output_dataset_id,
                output_dir=output_dir,
                output_dataset_name=output_dataset_name,
                total_images=total_images,
                tags_by_filename=tags_by_filename,
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
            time.sleep(POLL_INTERVAL_SECONDS)


def start_auto_annotation_worker() -> None:
    """在后台线程中启动自动标注 worker。"""

    thread = threading.Thread(target=_worker_loop, name="auto-annotation-worker", daemon=True)
    thread.start()
    logger.info("Auto-annotation worker thread started: {}", thread.name)
