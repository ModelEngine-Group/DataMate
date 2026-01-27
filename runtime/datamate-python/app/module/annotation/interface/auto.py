"""FastAPI routes for Auto Annotation tasks.

These routes back the frontend AutoAnnotation module:
  - GET  /api/annotation/auto
  - POST /api/annotation/auto
  - DELETE /api/annotation/auto/{task_id}
  - GET  /api/annotation/auto/{task_id}/status (simple wrapper)

"""
from __future__ import annotations

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.annotation_management import LabelingProject, AutoAnnotationTask
from app.module.shared.schema import StandardResponse
from app.module.dataset import DatasetManagementService
from app.core.logging import get_logger
from app.core.config import settings

from ..schema.auto import (
    CreateAutoAnnotationTaskRequest,
    AutoAnnotationTaskResponse,
    AutoAnnotationConfig,
    UpdateAutoAnnotationTaskFilesRequest,
    ImportFromLabelStudioRequest,
)
from ..service.auto import AutoAnnotationTaskService
from ..service.mapping import DatasetMappingService
from ..service.prediction import PredictionSyncService
from ..service.sync import SyncService
from ..client import LabelStudioClient


router = APIRouter(
    prefix="/auto",
    tags=["annotation/auto"],
)

logger = get_logger(__name__)
service = AutoAnnotationTaskService()


# COCO 80 类别映射（需与 runtime/ops/annotation/image_object_detection_bounding_box/process.py 保持一致）
COCO_CLASS_MAP: Dict[int, str] = {
    0: "Person",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    4: "Airplane",
    5: "Bus",
    6: "Train",
    7: "Truck",
    8: "Boat",
    9: "Traffic Light",
    10: "Fire Hydrant",
    11: "Stop Sign",
    12: "Parking Meter",
    13: "Bench",
    14: "Bird",
    15: "Cat",
    16: "Dog",
    17: "Horse",
    18: "Sheep",
    19: "Cow",
    20: "Elephant",
    21: "Bear",
    22: "Zebra",
    23: "Giraffe",
    24: "Backpack",
    25: "Umbrella",
    26: "Handbag",
    27: "Tie",
    28: "Suitcase",
    29: "Frisbee",
    30: "Skis",
    31: "Snowboard",
    32: "Sports Ball",
    33: "Kite",
    34: "Baseball Bat",
    35: "Baseball Glove",
    36: "Skateboard",
    37: "Surfboard",
    38: "Tennis Racket",
    39: "Bottle",
    40: "Wine Glass",
    41: "Cup",
    42: "Fork",
    43: "Knife",
    44: "Spoon",
    45: "Bowl",
    46: "Banana",
    47: "Apple",
    48: "Sandwich",
    49: "Orange",
    50: "Broccoli",
    51: "Carrot",
    52: "Hot Dog",
    53: "Pizza",
    54: "Donut",
    55: "Cake",
    56: "Chair",
    57: "Couch",
    58: "Potted Plant",
    59: "Bed",
    60: "Dining Table",
    61: "Toilet",
    62: "TV",
    63: "Laptop",
    64: "Mouse",
    65: "Remote",
    66: "Keyboard",
    67: "Cell Phone",
    68: "Microwave",
    69: "Oven",
    70: "Toaster",
    71: "Sink",
    72: "Refrigerator",
    73: "Book",
    74: "Clock",
    75: "Vase",
    76: "Scissors",
    77: "Teddy Bear",
    78: "Hair Drier",
    79: "Toothbrush",
}


def _build_label_studio_config_from_auto_config(config: AutoAnnotationConfig) -> str:
    """根据自动标注配置生成 Label Studio XML 配置。

    - 使用 Image + RectangleLabels 模板；
    - label 列表来自 targetClasses 对应的 COCO 类别；
      targetClasses 为空时表示全部 80 类。
    """

    # 目标类别 ID 列表；为空则使用全部 COCO 类别
    if config.target_classes:
        class_ids = sorted({int(cid) for cid in config.target_classes})
    else:
        class_ids = sorted(COCO_CLASS_MAP.keys())

    labels = []
    for cid in class_ids:
        name = COCO_CLASS_MAP.get(int(cid), f"class_{cid}")
        labels.append(name)

    lines = [
        "<View>",
        '  <Image name="image" value="$image"/>',
        '  <RectangleLabels name="label" toName="image">',
    ]

    for name in labels:
        # Label value 需要与 YOLO 导出的 annotations["detections"][*]["label"] 一致
        lines.append(f'    <Label value="{name}"/>')

    lines.extend([
        "  </RectangleLabels>",
        "</View>",
    ])
    return "\n".join(lines)


async def _ensure_ls_mapping_for_auto_task(
    db: AsyncSession,
    *,
    dataset_id: str,
    dataset_name: Optional[str],
    config: AutoAnnotationConfig,
    task_name: str,
    file_ids: Optional[List[str]] = None,
    auto_task_id: Optional[str] = None,
    delete_orphans: bool = False,
) -> Optional[str]:
    """确保给定数据集存在一个 Label Studio 项目映射，并按需同步子集文件。

    说明：
    - 仍然保持「1 个数据集 -> 多个 LS 项目」的模型不变；
    - 如果已有映射，则复用最新项目，仅根据 file_ids 进行增量同步；
    - 如果没有映射，则创建新项目 + 本地存储 + 映射，再按照 file_ids/全量进行一次同步。

    返回 Label Studio project_id，失败时返回 None。
    """

    mapping_service = DatasetMappingService(db)
    dm_client = DatasetManagementService(db)
    ls_client = LabelStudioClient(
        base_url=settings.label_studio_base_url,
        token=settings.label_studio_user_token,
    )
    sync_service = SyncService(dm_client, ls_client, mapping_service)

    # 获取主数据集信息（用于项目描述等）。
    # 如果获取失败，不再中断流程，只在描述中降级使用 dataset_id/dataset_name。
    dataset = None
    try:
        dataset = await dm_client.get_dataset(dataset_id)
    except Exception as e:  # pragma: no cover - 容错
        logger.warning(
            "Failed to fetch dataset info from DM when creating LS project %s: %s",
            dataset_id,
            e,
        )

    existing = await mapping_service.get_mappings_by_dataset_id(dataset_id)
    # 仅在同一数据集下找到“名称等于任务名”的映射时才复用，
    # 确保每个自动标注任务对应独立的 LS 项目。
    target_mapping = None
    for m in existing:
        if m.name == task_name:
            target_mapping = m
            break

    if target_mapping is not None:
        mapping = target_mapping
        project_id = mapping.labeling_project_id
        logger.info(
            "Reuse existing Label Studio mapping for dataset %s and auto task '%s': project_id=%s",
            dataset_id,
            task_name,
            project_id,
        )
    else:
        logger.info(
            "No existing Label Studio mapping for dataset %s and auto task '%s', creating one",
            dataset_id,
            task_name,
        )

        # Label Studio 项目标题与自动标注任务名称保持一致（DM 侧映射 name=task_name），
        # 但 Label Studio 要求 title 至少 3 个字符，这里只对传给 LS 的 title 做安全填充，
        # 映射表中的 name 仍然保存为原始 task_name，方便在 DM 中一一对应。
        project_name = task_name
        # 构造项目描述，尽量带上数据集名称，但获取失败时回退到 dataset_id
        dataset_display_name = None
        if dataset is not None:
            dataset_display_name = getattr(dataset, "name", None) or str(dataset_id)
        elif dataset_name:
            dataset_display_name = dataset_name
        else:
            dataset_display_name = str(dataset_id)

        project_description = (
            f"Auto annotation project for dataset {dataset_display_name} ({dataset_id}), task '{task_name}'"
        )

        label_config = _build_label_studio_config_from_auto_config(config)

        # 为满足 LS 对 title 长度的校验，确保传入的 title 至少 3 个字符
        safe_title = project_name if project_name and len(project_name) >= 3 else (project_name or "")
        if len(safe_title) < 3:
            safe_title = safe_title.ljust(3, "_")

        project_data = await ls_client.create_project(
            title=safe_title,
            description=project_description,
            label_config=label_config,
        )
        if not project_data:
            logger.error("Failed to create Label Studio project for dataset %s", dataset_id)
            return None

        project_id = project_data.get("id")
        logger.info("Created Label Studio project %s for dataset %s", project_id, dataset_id)

        # 配置主数据集的本地存储，复用与手动映射相同的路径规则
        local_storage_path = f"{settings.label_studio_local_document_root}/{dataset_id}"
        storage_result = await ls_client.create_local_storage(
            project_id=int(project_id),
            path=local_storage_path,
            title="Dataset_BLOB",
            use_blob_urls=True,
            description=f"Local storage for dataset {dataset_display_name}",
        )
        if not storage_result:
            logger.warning(
                "Failed to configure local storage for auto task project %s (dataset %s)",
                project_id,
                dataset_id,
            )

        # 将项目与数据集写入映射表，并在 configuration 中记录 autoTaskId 关联关系
        config_payload: Dict[str, Any] = {}
        if auto_task_id:
            config_payload["autoTaskId"] = auto_task_id
            config_payload["autoTaskName"] = task_name

        labeling_project = LabelingProject(
            dataset_id=dataset_id,
            labeling_project_id=str(project_id),
            name=project_name,
            configuration=config_payload or None,
        )
        mapping = await mapping_service.create_mapping(labeling_project)

    # 无论是复用还是新建，都根据 file_ids 做一次文件同步：
    # - 未指定 file_ids 时，同步主数据集的全部文件；
    # - 指定 file_ids 时，允许跨多个数据集，最终都汇总到同一个 LS 项目下。
    try:
        from typing import Set as _Set
        from sqlalchemy import select
        from app.db.models.dataset_management import DatasetFiles

        if not file_ids:
            # 兼容老逻辑：未指定 file_ids 时，同步整个主数据集
            await sync_service.sync_files(
                mapping,
                100,
                delete_orphans=delete_orphans,
            )
        else:
            # 按 file_ids 反查所属数据集：dataset_id -> set(file_ids)
            stmt = (
                select(DatasetFiles.dataset_id, DatasetFiles.id)
                .where(DatasetFiles.id.in_(file_ids))
            )
            result = await db.execute(stmt)
            rows = result.fetchall()

            grouped: Dict[str, _Set[str]] = {}
            resolved_ids: _Set[str] = set()

            for ds_id, fid in rows:
                if not ds_id or not fid:
                    continue
                fid_str = str(fid)
                grouped.setdefault(str(ds_id), set()).add(fid_str)
                resolved_ids.add(fid_str)

            # 将未能解析到数据集的文件，全部归入主数据集，避免丢失
            unresolved_ids = {str(fid) for fid in file_ids} - resolved_ids
            if unresolved_ids:
                logger.warning(
                    "Some file_ids could not be resolved to dataset_id when syncing auto task files: %s",
                    ",".join(sorted(unresolved_ids)),
                )
                grouped.setdefault(str(dataset_id), set()).update(unresolved_ids)

            # 为所有涉及到的额外数据集提前配置本地存储，避免首次引用该数据集但尚未
            # 在任意项目中注册 local storage 时，/data/local-files 返回 404。
            try:
                for extra_ds_id in grouped.keys():
                    # 主数据集已在上方配置过，这里只为额外数据集创建存储记录
                    if str(extra_ds_id) == str(dataset_id):
                        continue

                    extra_local_storage_path = f"{settings.label_studio_local_document_root}/{extra_ds_id}"
                    extra_storage_result = await ls_client.create_local_storage(
                        project_id=int(project_id),
                        path=extra_local_storage_path,
                        title=f"Dataset_BLOB_{extra_ds_id}",
                        use_blob_urls=True,
                        description=f"Local storage for dataset {extra_ds_id} (multi-dataset auto task)",
                    )
                    if not extra_storage_result:
                        logger.warning(
                            "Failed to configure extra local storage for auto task project %s (dataset %s)",
                            project_id,
                            extra_ds_id,
                        )
                    else:
                        logger.info(
                            "Extra local storage configured for auto task project %s: %s",
                            project_id,
                            extra_local_storage_path,
                        )
            except Exception as e:
                logger.warning(
                    "Error while configuring extra local storage for auto task project %s: %s",
                    project_id,
                    e,
                )

            if not grouped:
                # 极端情况：完全无法解析，退回到仅按主数据集＋给定 file_ids 同步
                await sync_service.sync_files(
                    mapping,
                    100,
                    allowed_file_ids={str(fid) for fid in file_ids},
                    delete_orphans=delete_orphans,
                )
            else:
                # 对每个涉及到的数据集，使用 override_dataset_id 将其文件同步到同一个项目
                for ds_id, ds_file_ids in grouped.items():
                    await sync_service.sync_files(
                        mapping,
                        100,
                        allowed_file_ids=ds_file_ids,
                        override_dataset_id=ds_id,
                        delete_orphans=delete_orphans,
                    )
    except Exception as e:  # pragma: no cover - 同步失败不影响项目创建
        logger.warning(
            "Failed to sync dataset files for auto task LS project %s: %s",
            project_id,
            e,
        )

    return str(project_id)




@router.get("", response_model=StandardResponse[List[AutoAnnotationTaskResponse]])
async def list_auto_annotation_tasks(
    db: AsyncSession = Depends(get_db),
):
    """获取自动标注任务列表。

    前端当前不传分页参数，这里直接返回所有未删除任务。
    """

    tasks = await service.list_tasks(db)
    return StandardResponse(
        code=200,
        message="success",
        data=tasks,
    )


@router.post("", response_model=StandardResponse[AutoAnnotationTaskResponse])
async def create_auto_annotation_task(
    request: CreateAutoAnnotationTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建自动标注任务。

    当前仅创建任务记录并置为 pending，实际执行由后续调度/worker 完成。
    """

    logger.info(
        "Creating auto annotation task: name=%s, dataset_id=%s, config=%s, file_ids=%s",
        request.name,
        request.dataset_id,
        request.config.model_dump(by_alias=True),
        request.file_ids,
    )

    # 尝试获取数据集名称和文件数量用于冗余字段，失败时不阻塞任务创建
    dataset_name = None
    total_images = 0
    try:
        dm_client = DatasetManagementService(db)
        # Service.get_dataset 返回 DatasetResponse，包含 name 和 fileCount
        dataset = await dm_client.get_dataset(request.dataset_id)
        if dataset is not None:
            dataset_name = dataset.name
            # 如果提供了 file_ids，则 total_images 为选中文件数；否则使用数据集文件数
            if request.file_ids:
                total_images = len(request.file_ids)
            else:
                total_images = getattr(dataset, "fileCount", 0) or 0
    except Exception as e:  # pragma: no cover - 容错
        logger.warning("Failed to fetch dataset name for auto task: %s", e)

    task = await service.create_task(
        db,
        request,
        dataset_name=dataset_name,
        total_images=total_images,
    )

    # 创建/复用一个与主数据集关联的 Label Studio 项目，
    # 并在该项目下为本次任务选中的所有文件（可跨多个数据集）创建任务。
    try:
        await _ensure_ls_mapping_for_auto_task(
            db,
            dataset_id=request.dataset_id,
            dataset_name=dataset_name,
            config=request.config,
            task_name=request.name,
            file_ids=[str(fid) for fid in (request.file_ids or [])],
            auto_task_id=task.id,
        )
    except Exception as e:  # pragma: no cover - 容错，不阻塞任务创建
        logger.warning(
            "Failed to ensure Label Studio mapping when creating auto task %s: %s",
            task.id,
            e,
        )

    return StandardResponse(
        code=200,
        message="success",
        data=task,
    )


@router.put("/{task_id}/files", response_model=StandardResponse[AutoAnnotationTaskResponse])
async def update_auto_annotation_task_files(
    task_id: str = Path(..., description="任务ID"),
    request: UpdateAutoAnnotationTaskFilesRequest = ...,  # 通过 body 传入 datasetId 与 fileIds
    db: AsyncSession = Depends(get_db),
):
    """更新自动标注任务所关联的数据集文件，并同步到 Label Studio。

    最新约定：
    1. 创建任务时选择的文件集合视为“基础集合”，后续编辑时不允许将其移除，只能追加新文件；
    2. runtime worker 仅对新增文件执行自动标注，历史文件结果和输出数据集保持不变；
    3. 编辑任务数据集时，仅将新增文件同步到 Label Studio，不再删除已有任务。
    """

    # 1. 获取现有任务（响应模型）以便读取当前配置
    existing = await service.get_task(db, task_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    # 1.1 计算旧文件集合与本次提交集合：
    #     - 旧集合视为“锁定”，不允许通过编辑接口移除；
    #     - 新集合与旧集合求并集后才会写回任务记录；
    #     - 仅对 (新集合 - 旧集合) 这一部分视为“新增文件”，用于后续 LS 同步。
    old_ids = {str(fid) for fid in (existing.file_ids or [])}
    requested_ids = {str(fid) for fid in (request.file_ids or [])}
    added_ids = sorted(requested_ids - old_ids)
    final_ids = sorted(old_ids | requested_ids)

    # datasetId 若未显式传入，则沿用原任务值
    dataset_id = request.dataset_id or existing.dataset_id

	# 2. 更新底层任务记录（ORM），重置状态与文件列表（文件集合为旧集合 ∪ 本次提交集合）
    updated = await service.update_task_files(
        db,
        task_id=task_id,
        dataset_id=str(dataset_id),
		file_ids=final_ids,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")

    # 3. 使用当前配置 + 新 file_ids 同步 LS 项目映射。
    #    解析失败时退回到一个默认配置（与其它接口保持一致）。
    try:
        auto_config = AutoAnnotationConfig.model_validate(existing.config)  # type: ignore[arg-type]
    except Exception as e:  # pragma: no cover - 降级使用默认配置
        logger.warning(
            "Failed to parse auto task config when updating LS mapping for task %s: %s",
            task_id,
            e,
        )
        auto_config = AutoAnnotationConfig(
            model_size="l",
            conf_threshold=0.5,
            target_classes=[],
        )

    # 仅在存在“新增文件”时，才将这部分文件同步到 Label Studio；
    # 不再删除 LS 中已有任务（delete_orphans=False）。
    if added_ids:
        try:
            await _ensure_ls_mapping_for_auto_task(
                db,
                dataset_id=str(dataset_id),
                dataset_name=updated.dataset_name,
                config=auto_config,
                task_name=updated.name,
                file_ids=added_ids,
                auto_task_id=updated.id,
                delete_orphans=False,
            )
        except Exception as e:  # pragma: no cover - 映射同步失败不阻塞前端
            logger.warning(
                "Failed to sync Label Studio mapping when updating auto task %s: %s",
                task_id,
                e,
            )

    return StandardResponse(
        code=200,
        message="success",
        data=updated,
    )


@router.get("/{task_id}/status", response_model=StandardResponse[AutoAnnotationTaskResponse])
async def get_auto_annotation_task_status(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取单个自动标注任务状态。

    前端当前主要通过列表轮询，这里提供按 ID 查询的补充接口。
    """

    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return StandardResponse(
        code=200,
        message="success",
        data=task,
    )


@router.get("/{task_id}/files", response_model=StandardResponse[List[Dict[str, Any]]])
async def get_auto_annotation_task_files(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """查询自动标注任务当前关联的 DM 文件列表。

    该接口主要用于前端“编辑任务数据集”弹窗的初始选中状态：
    - 若任务记录中存在 file_ids，则按这些 ID 精确查询；
    - 若 file_ids 为空，则回退为查询主数据集下的全部 ACTIVE 文件。

    返回的每一项仅包含前端需要的基础字段，避免一次性返回过多无关信息。
    """

    from sqlalchemy import select  # 本地导入避免循环依赖
    from app.db.models.dataset_management import DatasetFiles, Dataset

    # 先获取任务，确保存在
    result = await db.execute(
        select(AutoAnnotationTask).where(
            AutoAnnotationTask.id == task_id,
            AutoAnnotationTask.deleted_at.is_(None),
        )
    )
    task_row = result.scalar_one_or_none()
    if not task_row:
        raise HTTPException(status_code=404, detail="Task not found")

    file_ids = getattr(task_row, "file_ids", None) or []
    dataset_id = getattr(task_row, "dataset_id", None)

    files_query = None
    params: Dict[str, Any] = {}

    if file_ids:
        # 按任务记录中的 file_ids 精确查询
        files_query = select(DatasetFiles).where(DatasetFiles.id.in_(file_ids))
    else:
        # 未显式记录 file_ids 时，回退为主数据集下所有 ACTIVE 文件
        if not dataset_id:
            return StandardResponse(code=200, message="success", data=[])
        files_query = select(DatasetFiles).where(
            DatasetFiles.dataset_id == dataset_id,
            DatasetFiles.status == "ACTIVE",
        )

    files_result = await db.execute(files_query)
    files = list(files_result.scalars().all())

    # 为涉及到的 dataset_id 一次性查询名称映射，方便前端展示
    dataset_ids = {str(f.dataset_id) for f in files if getattr(f, "dataset_id", None)}
    dataset_name_map: Dict[str, str] = {}
    if dataset_ids:
        ds_result = await db.execute(
            select(Dataset.id, Dataset.name).where(Dataset.id.in_(dataset_ids))
        )
        for ds_id, ds_name in ds_result.fetchall():
            dataset_name_map[str(ds_id)] = ds_name or ""

    data: List[Dict[str, Any]] = []
    for f in files:
        fid = str(getattr(f, "id"))
        ds_id = str(getattr(f, "dataset_id")) if getattr(f, "dataset_id", None) else None
        item: Dict[str, Any] = {
            "id": fid,
            "datasetId": ds_id,
            "datasetName": dataset_name_map.get(ds_id or "", ""),
            "fileName": getattr(f, "file_name", ""),
            "fileSize": int(getattr(f, "file_size", 0) or 0),
            "filePath": getattr(f, "file_path", ""),
        }
        data.append(item)

    return StandardResponse(code=200, message="success", data=data)


@router.get("/{task_id}/label-studio-project", response_model=StandardResponse[Dict[str, str]])
async def get_auto_annotation_label_studio_project(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取与指定自动标注任务关联的 Label Studio 项目。

    优先依据 LabelingProject.configuration.autoTaskId 进行精确匹配，
    若未找到，则回退为在同一数据集下按项目名称 (name == task.name) 匹配。
    """

    # 1. 获取自动标注任务，确保存在
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    from sqlalchemy import select  # 本地导入以避免循环依赖问题

    # 2. 查询该数据集下所有未删除的 LabelingProject
    result = await db.execute(
        select(LabelingProject)
        .where(
            LabelingProject.dataset_id == task.dataset_id,
            LabelingProject.deleted_at.is_(None),
        )
        .order_by(LabelingProject.created_at.desc())
    )
    projects = list(result.scalars().all())

    target: Optional[LabelingProject] = None

    # 2.1 优先根据 configuration.autoTaskId 精确匹配
    for proj in projects:
        cfg = getattr(proj, "configuration", None) or {}
        if isinstance(cfg, dict) and cfg.get("autoTaskId") == task_id:
            target = proj
            break

    # 2.2 若未命中，则回退为按名称匹配（与当前自动任务同名的项目）
    if target is None:
        for proj in projects:
            if proj.name == task.name:
                target = proj
                break

    # 2.3 如果仍未找到，则尝试自动为该任务创建一个隐藏的标注项目
    if target is None:
        try:
            try:
                auto_config = AutoAnnotationConfig.model_validate(task.config)
            except Exception as e:  # pragma: no cover - 容错，使用默认配置
                logger.warning(
                    "Failed to parse auto task config when auto-creating LS project: %s",
                    e,
                )
                auto_config = AutoAnnotationConfig(
                    model_size="l",
                    conf_threshold=0.5,
                    target_classes=[],
                )

            project_id = await _ensure_ls_mapping_for_auto_task(
                db,
                dataset_id=task.dataset_id,
                dataset_name=task.dataset_name,
                config=auto_config,
                task_name=task.name,
                file_ids=[str(fid) for fid in (task.file_ids or [])],
                auto_task_id=task.id,
            )

            if project_id:
                # 刚创建的项目此时还不在 projects 列表中，这里根据 labeling_project_id 重新查询一次
                result2 = await db.execute(
                    select(LabelingProject).where(
                        LabelingProject.labeling_project_id == str(project_id),
                        LabelingProject.deleted_at.is_(None),
                    )
                )
                target = result2.scalar_one_or_none()
        except Exception as e:  # pragma: no cover - 创建失败不抛出到前端
            logger.warning(
                "Failed to auto-create LS project when resolving auto task %s: %s",
                task_id,
                e,
            )

    if target is None:
        raise HTTPException(
            status_code=404,
            detail="Label Studio project not found for this auto task",
        )

    data = {
        "projectId": str(target.labeling_project_id),
        "name": target.name or "",
        "datasetId": str(target.dataset_id),
    }

    return StandardResponse(code=200, message="success", data=data)


@router.delete("/{task_id}", response_model=StandardResponse[bool])
async def delete_auto_annotation_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除（软删除）自动标注任务，并清理可能存在的自动创建标注项目。

    逻辑：
    1. 先根据 task_id 查询任务，拿到 dataset_id；
    2. 软删除自动标注任务记录；
    3. 尝试为该数据集查找名称以 " - 自动标注" 结尾的映射（LabelingProject）；
       若存在，则删除对应的 Label Studio 项目并软删除映射记录。

    这样即使后台为自动标注创建了一个“隐藏”的标注项目，在删除自动标注任务时也会一并清理，
    避免数据库和 Label Studio 中遗留孤立项目。
    """

    # 1. 先获取任务，确保存在并拿到 dataset_id
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    dataset_id = task.dataset_id

    # 2. 软删除自动标注任务
    ok = await service.soft_delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")

    # 3. 尝试清理该数据集下与本自动标注任务关联的 Label Studio 项目
    try:  # 清理失败不影响主流程
        mapping_service = DatasetMappingService(db)
        mappings = await mapping_service.get_mappings_by_dataset_id(dataset_id)

        if mappings:
            ls_client = LabelStudioClient(
                base_url=settings.label_studio_base_url,
                token=settings.label_studio_user_token,
            )

            for mapping in mappings:
                # 仅删除“名称与当前自动标注任务名称相同”的项目，
                # 同时兼容老版本以 " - 自动标注" 结尾的自动创建项目。
                name = (mapping.name or "") if hasattr(mapping, "name") else ""
                if name != task.name and not name.endswith(" - 自动标注"):
                    continue

                labeling_project_id = mapping.labeling_project_id

                # 删除 Label Studio 项目（忽略失败）
                try:
                    logger.info(
                        "Deleting Label Studio project %s (name=%s) for dataset %s when deleting auto task %s",
                        labeling_project_id,
                        name,
                        dataset_id,
                        task_id,
                    )
                    await ls_client.delete_project(int(labeling_project_id))
                except Exception as e:  # pragma: no cover - 清理失败不影响主流程
                    logger.warning(
                        "Failed to delete Label Studio project %s for dataset %s: %s",
                        labeling_project_id,
                        dataset_id,
                        e,
                    )

                # 软删除映射记录
                try:
                    await mapping_service.soft_delete_mapping(mapping.id)
                except Exception as e:  # pragma: no cover
                    logger.warning(
                        "Failed to soft delete mapping %s for auto dataset %s: %s",
                        mapping.id,
                        dataset_id,
                        e,
                    )
    except Exception as e:  # pragma: no cover
        logger.warning(
            "Failed to cleanup auto-created labeling projects when deleting auto task %s: %s",
            task_id,
            e,
        )

    return StandardResponse(
        code=200,
        message="success",
        data=True,
    )


@router.get("/{task_id}/download")
async def download_auto_annotation_result(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """下载指定自动标注任务的结果 ZIP。"""

    import io
    import os
    import zipfile
    import tempfile

    # 复用服务层获取任务信息
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.output_path:
        raise HTTPException(status_code=400, detail="Task has no output path")

    output_dir = task.output_path
    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_fd)

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, output_dir)
                zf.write(file_path, arcname)

    file_size = os.path.getsize(tmp_path)
    if file_size == 0:
        raise HTTPException(status_code=500, detail="Generated ZIP is empty")

    def iterfile():
        with open(tmp_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk

    filename = f"{task.name}_annotations.zip"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(file_size),
    }

    return StreamingResponse(iterfile(), media_type="application/zip", headers=headers)


@router.post("/{task_id}/sync-label-studio", response_model=StandardResponse[int])
async def sync_auto_annotation_to_label_studio(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """将指定自动标注任务的检测结果，同步到 Label Studio 作为 predictions。

    流程：
    1. 根据 task_id 查询自动标注任务信息，校验状态为 completed，且存在输出目录；
    2. 基于任务的 dataset_id 查找对应的数据集映射，获取 Label Studio project_id；
    3. 使用 PredictionSyncService 读取 `output_path/annotations` 下的 JSON，
       将检测结果转换为 predictions 写入对应的 Label Studio 任务。

    返回成功创建 prediction 的任务数量。
    """

    # 1. 获取并校验自动标注任务
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task is not completed yet")

    if not task.output_path:
        raise HTTPException(status_code=400, detail="Task has no output path")

    import os

    output_dir = task.output_path
    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    annotations_dir = os.path.join(output_dir, "annotations")
    if not os.path.isdir(annotations_dir):
        raise HTTPException(status_code=404, detail="Annotations directory not found")

    # 2. 查找或自动创建与主数据集关联的 Label Studio 项目。
    #    项目下的任务可能来自多个数据集，但在 DataMate 中仍然以主数据集进行归类，
    #    以保持与手动标注映射模型的一致性。
    mapping_service = DatasetMappingService(db)
    mappings = await mapping_service.get_mappings_by_dataset_id(task.dataset_id)

    project_id: Optional[str] = None
    # 优先复用 configuration.autoTaskId 关联的项目，其次按名称匹配，
    # 保证每个自动标注任务对应一个独立项目。
    for m in mappings:
        cfg = getattr(m, "configuration", None) or {}
        if isinstance(cfg, dict) and cfg.get("autoTaskId") == task.id:
            project_id = str(m.labeling_project_id)
            break

    if project_id is None:
        for m in mappings:
            if m.name == task.name:
                project_id = str(m.labeling_project_id)
                break

    if project_id is None:
        # 尚未为该自动标注任务创建过标注项目，则基于自动标注配置自动创建
        try:
            auto_config = AutoAnnotationConfig.model_validate(task.config)
        except Exception as e:  # pragma: no cover - 降级使用默认配置
            logger.warning("Failed to parse auto task config when creating LS project: %s", e)
            auto_config = AutoAnnotationConfig(
                model_size="l",
                conf_threshold=0.5,
                target_classes=[],
            )

        project_id = await _ensure_ls_mapping_for_auto_task(
            db,
            dataset_id=task.dataset_id,
            dataset_name=task.dataset_name,
            config=auto_config,
            task_name=task.name,
            file_ids=[str(fid) for fid in (task.file_ids or [])],
            auto_task_id=task.id,
        )

        if not project_id:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to create Label Studio project for this dataset "
                    "when syncing auto annotation results."
                ),
            )

    # 3. 调用 PredictionSyncService 将 YOLO JSON 推送为 predictions
    ls_client = LabelStudioClient(
        base_url=settings.label_studio_base_url,
        token=settings.label_studio_user_token,
    )
    sync_service = PredictionSyncService(ls_client)
    created_count = await sync_service.sync_predictions_from_dir(
        project_id=str(project_id),
        annotations_dir=annotations_dir,
    )

    return StandardResponse(
        code=200,
        message="success",
        data=created_count,
    )


@router.post("/{task_id}/sync-label-studio-back", response_model=StandardResponse[bool])
async def import_from_label_studio_to_dataset(
    task_id: str = Path(..., description="任务ID"),
    body: ImportFromLabelStudioRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """将指定自动标注任务在 Label Studio 中的标注结果导回到某个数据集。

    行为说明：
    - 基于自动标注任务找到/创建对应的 Label Studio 项目；
    - 调用 Label Studio 项目导出接口，按 exportFormat 下载完整导出文件；
    - 将该导出文件作为一个普通数据集文件写入 targetDatasetId 对应的数据集目录；
    - 不解析每条标注、不修改现有 tags，仅作为“标注导出工件”落盘，方便后续人工使用。
    """

    import os
    import tempfile
    from datetime import datetime

    if body is None:
        raise HTTPException(status_code=400, detail="Request body is required")

    # 1. 获取并校验自动标注任务
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 2. 确定目标数据集：若请求体未显式指定，则使用自动标注任务绑定的数据集
    dm_service = DatasetManagementService(db)
    target_dataset_id = body.target_dataset_id or task.dataset_id
    dataset = await dm_service.get_dataset(target_dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Target dataset not found")

    # 3. 查找或创建与该自动标注任务关联的 Label Studio 项目
    mapping_service = DatasetMappingService(db)
    mappings = await mapping_service.get_mappings_by_dataset_id(task.dataset_id)

    project_id: Optional[str] = None
    for m in mappings:
        cfg = getattr(m, "configuration", None) or {}
        if isinstance(cfg, dict) and cfg.get("autoTaskId") == task.id:
            project_id = str(m.labeling_project_id)
            break

    if project_id is None:
        for m in mappings:
            if m.name == task.name:
                project_id = str(m.labeling_project_id)
                break

    if project_id is None:
        # 与前向同步逻辑保持一致：如无现成项目则按自动标注配置自动创建。
        try:
            auto_config = AutoAnnotationConfig.model_validate(task.config)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to parse auto task config when creating LS project for back sync: %s", e)
            auto_config = AutoAnnotationConfig(
                model_size="l",
                conf_threshold=0.5,
                target_classes=[],
            )

        project_id = await _ensure_ls_mapping_for_auto_task(
            db,
            dataset_id=task.dataset_id,
            dataset_name=task.dataset_name,
            config=auto_config,
            task_name=task.name,
            file_ids=[str(fid) for fid in (task.file_ids or [])],
            auto_task_id=task.id,
        )

        if not project_id:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to create or resolve Label Studio project for this auto task "
                    "when importing annotations back."
                ),
            )

    # 4. 调用 Label Studio 导出接口
    ls_client = LabelStudioClient(
        base_url=settings.label_studio_base_url,
        token=settings.label_studio_user_token,
    )

    export_format = (body.export_format or "JSON").upper()

    # 简单根据导出格式推断文件扩展名，仅用于提高可读性
    ext_map = {
        "JSON": ".json",
        "JSON_MIN": ".json",
        "CSV": ".csv",
        "TSV": ".tsv",
        "COCO": ".json",
        "YOLO": ".json",
        "YOLOV8": ".json",
    }
    file_ext = ext_map.get(export_format, ".json")

    content = await ls_client.export_project(int(project_id), export_type=export_format)
    if content is None or len(content) == 0:
        raise HTTPException(status_code=500, detail="Failed to export project from Label Studio")

    # 5. 将导出结果写入临时文件，再通过 DatasetManagementService 复制到数据集目录并注册记录
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=file_ext)
    os.close(tmp_fd)

    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        # 生成一个具备时间戳的文件名，避免与现有文件冲突；
        # 若前端提供了自定义文件名，则优先使用其主体部分，再附加正确的扩展名。
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        def _sanitize_base_name(raw: str) -> str:
            # 去掉路径分隔符，仅保留最后一段
            name = (raw or "").strip().replace("\\", "/").split("/")[-1]
            # 去掉用户自带的扩展名，避免与服务器推断的后缀冲突
            if "." in name:
                name = name.rsplit(".", 1)[0]
            # 退回到默认前缀
            return name or f"ls_export_{project_id}_{timestamp}"

        if getattr(body, "file_name", None):
            base_stem = _sanitize_base_name(body.file_name)  # type: ignore[arg-type]
            base_name = f"{base_stem}{file_ext}"
        else:
            base_name = f"ls_export_{project_id}_{timestamp}{file_ext}"

        # DatasetManagementService.add_files_to_dataset 会使用源文件名决定目标文件名，
        # 因此这里将临时文件重命名为期望的可读名称后再导入。
        tmp_dir = os.path.dirname(tmp_path)
        target_tmp_path = os.path.join(tmp_dir, base_name)
        os.replace(tmp_path, target_tmp_path)

        # 统一写入源数据集下的 "标注数据" 目录，便于管理导出工件
        await dm_service.add_files_to_dataset_subdir(target_dataset_id, [target_tmp_path], "标注数据")
    finally:
        # 清理临时文件（若仍存在）
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        # 也尝试清理重命名后的临时文件
        if "target_tmp_path" in locals() and os.path.exists(target_tmp_path):
            try:
                os.remove(target_tmp_path)
            except Exception:
                pass

    return StandardResponse(code=200, message="success", data=True)
