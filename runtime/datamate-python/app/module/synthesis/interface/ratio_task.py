import asyncio
import uuid
from typing import Set
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, func, delete, select

from app.core.logging import get_logger
from app.db.models import Dataset
from app.db.session import get_db
from app.module.dataset import DatasetManagementService
from app.module.shared.schema import StandardResponse
from app.module.synthesis.schema.ratio_task import (
    CreateRatioTaskResponse,
    CreateRatioTaskRequest,
    PagedRatioTaskResponse,
    RatioTaskItem,
    TargetDatasetInfo,
    RatioTaskDetailResponse,
)
from app.module.synthesis.service.ratio_task import RatioTaskService
from app.db.models.ratio_task import RatioInstance, RatioRelation, RatioRelation as RatioRelationModel

router = APIRouter(
    prefix="/ratio-task",
    tags=["synthesis/ratio-task"],
)
logger = get_logger(__name__)



@router.post("", response_model=StandardResponse[CreateRatioTaskResponse], status_code=200)
async def create_ratio_task(
    req: CreateRatioTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    创建配比任务

    Path: /api/synthesis/ratio-task
    """
    try:
        # 校验 config 中的 dataset_id 是否存在
        dm_service = DatasetManagementService(db)
        source_types = await get_dataset_types(dm_service, req)

        await valid_exists(db, req)

        # 创建目标数据集：名称使用“<任务名称>-配比生成-时间戳”
        target_dataset_name = f"{req.name}-配比生成-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        target_type = get_target_dataset_type(source_types)

        target_dataset = Dataset(
            id=str(uuid.uuid4()),
            name=target_dataset_name,
            description=req.description or "",
            dataset_type=target_type,
            status="DRAFT",
        )
        target_dataset.path = f"/dataset/{target_dataset.id}"
        db.add(target_dataset)
        await db.flush()  # 获取 target_dataset.id

        service = RatioTaskService(db)
        instance = await service.create_task(
            name=req.name,
            description=req.description,
            totals=int(req.totals),
            ratio_method=req.ratio_method,
            config=[
                {
                    "dataset_id": item.dataset_id,
                    "counts": int(item.counts),
                    "filter_conditions": item.filter_conditions,
                }
                for item in req.config
            ],
            target_dataset_id=target_dataset.id,
        )

        # 异步执行配比任务（支持 DATASET / TAG）
        asyncio.create_task(RatioTaskService.execute_dataset_ratio_task(instance.id))

        return StandardResponse(
            code=200,
            message="success",
            data=CreateRatioTaskResponse(
                id=instance.id,
                name=instance.name,
                description=instance.description,
                totals=instance.totals or 0,
                ratio_method=instance.ratio_method or req.ratio_method,
                status=instance.status or "PENDING",
                config=req.config,
                targetDataset=TargetDatasetInfo(
                    id=str(target_dataset.id),
                    name=str(target_dataset.name),
                    datasetType=str(target_dataset.dataset_type),
                    status=str(target_dataset.status),
                )
            )
        )
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create ratio task: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=StandardResponse[PagedRatioTaskResponse], status_code=200)
async def list_ratio_tasks(
    page: int = 1,
    size: int = 10,
    name: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """分页查询配比任务，支持名称与状态过滤"""
    try:
        query = select(RatioInstance)
        # filters
        if name:
            # simple contains filter
            query = query.where(RatioInstance.name.like(f"%{name}%"))
        if status:
            query = query.where(RatioInstance.status == status)

        # count
        count_q = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_q)).scalar_one()

        # page (1-based)
        page_index = max(page, 1) - 1
        query = query.order_by(RatioInstance.created_at.desc()).offset(page_index * size).limit(size)
        result = await db.execute(query)
        items = result.scalars().all()

        # map to DTOs and attach dataset name
        # preload datasets
        ds_ids = {i.target_dataset_id for i in items if i.target_dataset_id}
        ds_map = {}
        if ds_ids:
            ds_res = await db.execute(select(Dataset).where(Dataset.id.in_(list(ds_ids))))
            for d in ds_res.scalars().all():
                ds_map[d.id] = d

        content: list[RatioTaskItem] = []
        for i in items:
            ds = ds_map.get(i.target_dataset_id) if i.target_dataset_id else None
            content.append(
                RatioTaskItem(
                    id=i.id,
                    name=i.name or "",
                    description=i.description,
                    status=i.status,
                    totals=i.totals,
                    ratio_method=i.ratio_method,
                    target_dataset_id=i.target_dataset_id,
                    target_dataset_name=(ds.name if ds else None),
                    created_at=str(i.created_at) if getattr(i, "created_at", None) else None,
                    updated_at=str(i.updated_at) if getattr(i, "updated_at", None) else None,
                )
            )

        total_pages = (total + size - 1) // size if size > 0 else 0
        return StandardResponse(
            code=200,
            message="success",
            data=PagedRatioTaskResponse(
                content=content,
                totalElements=total,
                totalPages=total_pages,
                page=page,
                size=size,
            ),
        )
    except Exception as e:
        logger.error(f"Failed to list ratio tasks: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("", response_model=StandardResponse[str], status_code=200)
async def delete_ratio_tasks(
    ids: list[str] = Query(..., description="要删除的配比任务ID列表"),
    db: AsyncSession = Depends(get_db),
):
    """删除配比任务，返回简单结果字符串。"""
    try:
        if not ids:
            raise HTTPException(status_code=400, detail="ids is required")

        # 先删除关联关系
        await db.execute(
            delete(RatioRelation).where(RatioRelation.ratio_instance_id.in_(ids))
        )
        # 再删除实例
        await db.execute(
            delete(RatioInstance).where(RatioInstance.id.in_(ids))
        )
        await db.commit()

        return StandardResponse(code=200, message="success", data="success")
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete ratio tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Fail to delete ratio task: {e}")


async def valid_exists(db: AsyncSession, req: CreateRatioTaskRequest) -> None:
    """校验配比任务名称不能重复（精确匹配，去除首尾空格）。"""
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="ratio task name is required")

    # 查询是否已存在同名任务
    ratio_task = await db.execute(select(RatioInstance.id).where(RatioInstance.name == name))
    exists = ratio_task.scalar_one_or_none()
    if exists is not None:
        logger.error(f"create ratio task failed: ratio task '{name}' already exists (id={exists})")
        raise HTTPException(status_code=400, detail=f"ratio task '{name}' already exists")


async def get_dataset_types(dm_service: DatasetManagementService, req: CreateRatioTaskRequest) -> Set[str]:
    source_types: Set[str] = set()
    for item in req.config:
        dataset = await dm_service.get_dataset(item.dataset_id)
        if not dataset:
            raise HTTPException(status_code=400, detail=f"dataset_id not found: {item.dataset_id}")
        else:
            dtype = getattr(dataset, "dataset_type", None) or getattr(dataset, "datasetType", None)
            source_types.add(str(dtype).upper())
    return source_types


def get_target_dataset_type(source_types: Set[str]) -> str:
    # 根据源数据集类型决定目标数据集类型
    # 规则：
    # 1) 若全部为 TEXT -> TEXT
    # 2) 若存在且仅存在一种介质类型（IMAGE/AUDIO/VIDEO），且无其它类型 -> 对应介质类型
    # 3) 其它情况 -> OTHER
    media_modalities = {"IMAGE", "AUDIO", "VIDEO"}
    target_type = "OTHER"
    if source_types == {"TEXT"}:
        target_type = "TEXT"
    else:
        media_involved = source_types & media_modalities
        if len(media_involved) == 1 and source_types == media_involved:
            # 仅有一种介质类型且无其它类型
            target_type = next(iter(media_involved))
    return target_type


@router.get("/{task_id}", response_model=StandardResponse[RatioTaskDetailResponse], status_code=200)
async def get_ratio_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取配比任务详情

    Path: /api/synthesis/ratio-task/{task_id}
    """
    try:
        # 查询任务实例
        instance_res = await db.execute(
            select(RatioInstance).where(RatioInstance.id == task_id)
        )
        instance = instance_res.scalar_one_or_none()
        if not instance:
            raise HTTPException(status_code=404, detail="Ratio task not found")

        # 查询关联的配比关系
        relations_res = await db.execute(
            select(RatioRelationModel).where(RatioRelationModel.ratio_instance_id == task_id)
        )
        relations = list(relations_res.scalars().all())

        # 查询目标数据集
        target_ds = None
        if instance.target_dataset_id:
            ds_res = await db.execute(
                select(Dataset).where(Dataset.id == instance.target_dataset_id)
            )
            target_ds = ds_res.scalar_one_or_none()

        # 构建响应
        config = [
            {
                "dataset_id": rel.source_dataset_id,
                "counts": str(rel.counts) if rel.counts is not None else "0",
                "filter_conditions": rel.filter_conditions or "",
            }
            for rel in relations
        ]

        target_dataset_info = {
            "id": str(target_ds.id) if target_ds else None,
            "name": target_ds.name if target_ds else None,
            "type": target_ds.dataset_type if target_ds else None,
            "status": target_ds.status if target_ds else None,
            "file_count": target_ds.file_count if target_ds else 0,
            "size_bytes": target_ds.size_bytes if target_ds else 0,
        }

        return StandardResponse(
            code=200,
            message="success",
            data=RatioTaskDetailResponse(
                id=instance.id,
                name=instance.name or "",
                description=instance.description,
                status=instance.status or "UNKNOWN",
                totals=instance.totals or 0,
                ratio_method=instance.ratio_method or "",
                config=config,
                target_dataset=target_dataset_info,
                created_at=instance.created_at,
                updated_at=instance.updated_at,
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get ratio task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
