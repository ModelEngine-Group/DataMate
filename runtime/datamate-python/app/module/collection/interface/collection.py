import math
import uuid
import shutil
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models import Dataset
from app.db.models.data_collection import CollectionTask, TaskExecution, CollectionTemplate
from app.db.session import get_db
from app.module.collection.client.datax_client import DataxClient
from app.module.collection.schema.collection import CollectionTaskBase, CollectionTaskCreate, converter_to_response, \
    convert_for_create, SyncMode
from app.module.collection.schedule import schedule_collection_task, remove_collection_task
from app.module.collection.service.collection import CollectionTaskService
from app.module.shared.schema import StandardResponse, PaginatedData

router = APIRouter(
    prefix="/tasks",
    tags=["data-collection/tasks"],
)
logger = get_logger(__name__)


@router.post("", response_model=StandardResponse[CollectionTaskBase], operation_id="create_collect_task", tags=["mcp"])
async def create_task(
    request: CollectionTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建归集任务"""
    try:
        template = await db.execute(select(CollectionTemplate).where(CollectionTemplate.id == request.template_id))
        template = template.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=400, detail="Template not found")

        task_id = str(uuid.uuid4())
        DataxClient.generate_datx_config(request.config, template, f"/dataset/local/{task_id}")
        task = convert_for_create(request, task_id)
        task.template_name = template.name
        dataset = None

        if request.dataset_name:
            target_dataset_id = uuid.uuid4()
            dataset = Dataset(
                id=str(target_dataset_id),
                name=request.dataset_name,
                description="",
                dataset_type=request.dataset_type.name,
                status="DRAFT",
                path=f"/dataset/{target_dataset_id}",
            )
            db.add(dataset)

        task_service = CollectionTaskService(db)
        task = await task_service.create_task(task, dataset)

        task = await db.execute(select(CollectionTask).where(CollectionTask.id == task.id))
        task = task.scalar_one_or_none()
        await db.commit()
        if task and task.sync_mode == SyncMode.SCHEDULED.value and task.schedule_expression:
            schedule_collection_task(task.id, task.schedule_expression)

        return StandardResponse(
            code=200,
            message="Success",
            data=converter_to_response(task)
        )
    except HTTPException:
        await db.rollback()
        raise
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create collection task: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=StandardResponse[PaginatedData[CollectionTaskBase]])
async def list_tasks(
    page: int = 1,
    size: int = 20,
    name: Optional[str] = Query(None, description="任务名称模糊查询"),
    db: AsyncSession = Depends(get_db)
):
    """分页查询归集任务"""
    try:
        # 构建查询条件
        page = page if page > 0 else 1
        size = size if size > 0 else 20
        query = select(CollectionTask)

        if name:
            query = query.where(CollectionTask.name.ilike(f"%{name}%"))

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # 分页查询
        offset = (page - 1) * size
        tasks = (await db.execute(
            query.order_by(CollectionTask.created_at.desc())
            .offset(offset)
            .limit(size)
        )).scalars().all()

        # 转换为响应模型
        items = [converter_to_response(task) for task in tasks]
        total_pages = math.ceil(total / size) if total > 0 else 0

        return StandardResponse(
            code=200,
            message="Success",
            data=PaginatedData(
                content=items,
                total_elements=total,
                total_pages=total_pages,
                page=page,
                size=size,
            )
        )

    except Exception as e:
        logger.error(f"Failed to list evaluation tasks: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("", response_model=StandardResponse[str], status_code=200)
async def delete_collection_tasks(
    ids: list[str] = Query(..., description="要删除的任务ID列表"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除归集任务

    Args:
        ids: 任务ID
        db: 数据库会话

    Returns:
        StandardResponse[str]: 删除结果
    """
    try:
        # 检查任务是否存在
        task_id = ids[0]
        task = await db.get(CollectionTask, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Collection task not found")

        # 删除任务执行记录
        await db.execute(
            TaskExecution.__table__.delete()
            .where(TaskExecution.task_id == task_id)
        )
        remove_collection_task(task_id)

        target_path = f"/dataset/local/{task_id}"
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        job_path = f"/flow/data-collection/{task_id}"
        if os.path.exists(job_path):
            shutil.rmtree(job_path)

        # 删除任务
        await db.delete(task)
        await db.commit()

        return StandardResponse(
            code=200,
            message="Collection task deleted successfully",
            data="success"
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete collection task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{task_id}", response_model=StandardResponse[CollectionTaskBase])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取归集任务详情"""
    try:
        # Query the task by ID
        task = await db.get(CollectionTask, task_id)
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID {task_id} not found"
            )

        return StandardResponse(
            code=200,
            message="Success",
            data=converter_to_response(task)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")
