import json
import math
import uuid
import shutil
import os
import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ErrorCodes, BusinessError, SuccessResponse, transaction
from app.core.logging import get_logger
from app.db.models import Dataset, DatasetFiles
from app.db.models.data_collection import CollectionTask, TaskExecution, CollectionTemplate
from app.db.session import get_db
from app.module.collection.client.datax_client import DataxClient
from app.module.collection.schema.collection import CollectionTaskBase, CollectionTaskCreate, CollectionTaskUpdate, converter_to_response, \
    convert_for_create, SyncMode
from app.module.collection.schedule import schedule_collection_task, remove_collection_task
from app.module.collection.service.collection import CollectionTaskService
from app.module.shared.schema import StandardResponse, PaginatedData, TaskStatus

router = APIRouter(
    prefix="/tasks",
    tags=["data-collection/tasks"],
)
logger = get_logger(__name__)


async def is_hard_link(file_path: str) -> bool:
    """检查文件是否是硬链接"""
    try:
        stat_info = await asyncio.to_thread(os.stat, file_path)
        # 如果链接数大于1，说明是硬链接
        return stat_info.st_nlink > 1
    except OSError:
        return False


async def convert_hardlink_to_real_file(file_path: str) -> bool:
    """
    将硬链接转换为实体文件
    通过读取并重新写入文件内容，创建一个独立的副本
    """
    try:
        # 创建临时文件
        temp_path = f"{file_path}.tmp"
        # 使用 shutil.copy2 创建副本（保留元数据）
        await asyncio.to_thread(shutil.copy2, file_path, temp_path)
        # 删除原文件（硬链接）
        await asyncio.to_thread(os.unlink, file_path)
        # 重命名临时文件为原文件名
        await asyncio.to_thread(os.replace, temp_path, file_path)
        return True
    except OSError as e:
        logger.warning(f"Failed to convert hard link to real file {file_path}: {e}")
        # 清理临时文件（如果存在）
        if os.path.exists(f"{file_path}.tmp"):
            try:
                await asyncio.to_thread(os.remove, f"{file_path}.tmp")
            except OSError:
                pass
        return False


async def convert_dataset_hardlinks_before_delete(task_id: str, db: AsyncSession) -> int:
    """
    删除归集任务前，将数据集中的硬链接文件转换为实体文件

    Args:
        task_id: 归集任务ID
        db: 数据库会话

    Returns:
        转换成功的文件数量
    """
    try:
        # 查找所有数据集文件（通过文件路径匹配任务ID）
        # 注意：归集任务的源文件路径是 tmp/dataset/{task_id}/
        # 我们需要找到数据集中所有以这个路径为源的文件
        source_prefix = f"tmp/dataset/{task_id}/"

        # 查询所有可能相关的数据集文件
        result = await db.execute(
            select(DatasetFiles).where(
                DatasetFiles.file_path.like(f"%/dataset/%"),
                DatasetFiles.status == "ACTIVE"
            )
        )
        dataset_files = result.scalars().all()

        converted_count = 0
        for dataset_file in dataset_files:
            file_path = dataset_file.file_path
            if not file_path:
                continue

            # 检查文件是否是硬链接
            if await is_hard_link(file_path):
                logger.info(f"Converting hard link to real file: {file_path}")
                success = await convert_hardlink_to_real_file(file_path)
                if success:
                    converted_count += 1
                else:
                    logger.warning(f"Failed to convert hard link: {file_path}")

        if converted_count > 0:
            logger.info(f"Converted {converted_count} hard link(s) to real file(s) for task {task_id}")

        return converted_count
    except Exception as e:
        logger.error(f"Error converting hard links for task {task_id}: {e}", exc_info=True)
        return 0


@router.post("", response_model=StandardResponse[CollectionTaskBase], operation_id="create_collect_task", tags=["mcp"])
async def create_task(
    request: CollectionTaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建归集任务"""
    template = await db.execute(select(CollectionTemplate).where(CollectionTemplate.id == request.template_id))
    template = template.scalar_one_or_none()
    if not template:
        raise BusinessError(ErrorCodes.COLLECTION_TEMPLATE_NOT_FOUND, data={"template_id": request.template_id})

    task_id = str(uuid.uuid4())
    DataxClient.generate_datx_config(request.config, template, f"/dataset/local/{task_id}")
    task = convert_for_create(request, task_id)
    task.template_name = template.name
    dataset = None

    async with transaction(db):
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

    # 事务已提交，执行调度
    if task and task.sync_mode == SyncMode.SCHEDULED.value and task.schedule_expression:
        schedule_collection_task(task.id, task.schedule_expression)

    return SuccessResponse(data=converter_to_response(task))


@router.get("", response_model=StandardResponse[PaginatedData[CollectionTaskBase]])
async def list_tasks(
    page: int = 1,
    size: int = 20,
    name: Optional[str] = Query(None, description="Fuzzy search by task name"),
    status: Optional[str] = Query(None, description="Filter by task status"),
    db: AsyncSession = Depends(get_db)
):
    """分页查询归集任务"""
    # 构建查询条件
    page = page if page > 0 else 1
    size = size if size > 0 else 20
    query = select(CollectionTask)

    if name:
        query = query.where(CollectionTask.name.ilike(f"%{name}%"))

    if status:
        query = query.where(CollectionTask.status == status)

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

    return SuccessResponse(
        data=PaginatedData(
            content=items,
            total_elements=total,
            total_pages=total_pages,
            page=page,
            size=size,
        )
    )


@router.post("/{task_id}/execute", response_model=StandardResponse[str], operation_id="execute_task")
async def execute_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """执行归集任务"""
    from app.module.collection.service.collection import CollectionTaskService

    # 验证任务是否存在
    task = await db.execute(select(CollectionTask).where(CollectionTask.id == task_id))
    task = task.scalar_one_or_none()
    if not task:
        raise BusinessError(ErrorCodes.COLLECTION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 调用服务执行任务
    await CollectionTaskService.run_async(task_id)

    return SuccessResponse(
        data=task_id
    )


@router.put("/{task_id}", response_model=StandardResponse[CollectionTaskBase], operation_id="update_task")
async def update_task(
    task_id: str,
    request: CollectionTaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    更新归集任务

    支持修改的字段：
    - description: 任务描述
    - schedule_expression: 定时表达式（仅 SCHEDULED 模式）
    - timeout_seconds: 超时时间
    - config: 任务配置

    状态限制：
    - DRAFT/PENDING: 可以修改所有字段
    - RUNNING: 不允许修改
    - FAILED: 可以修改，修改后可重新执行
    - COMPLETED: ONCE 模式不允许修改，SCHEDULED 模式可以修改

    Args:
        task_id: 任务ID
        request: 更新请求
        db: 数据库会话

    Returns:
        更新后的任务信息
    """
    # 查询任务
    task = await db.get(CollectionTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.COLLECTION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 检查任务状态，RUNNING 状态不允许修改
    if task.status == TaskStatus.RUNNING.name:
        raise BusinessError(
            ErrorCodes.VALIDATION_ERROR,
            data={"task_id": task_id, "current_status": task.status}
        )

    # 检查任务同步模式，ONCE 模式已完成的不允许修改
    if task.sync_mode == SyncMode.ONCE.name and task.status == TaskStatus.COMPLETED.name:
        raise BusinessError(
            ErrorCodes.VALIDATION_ERROR,
            data={"task_id": task_id, "current_status": task.status}
        )

    # 验证 schedule_expression 只能由 SCHEDULED 模式修改
    if request.schedule_expression is not None and task.sync_mode != SyncMode.SCHEDULED.name:
        raise BusinessError(
            ErrorCodes.VALIDATION_ERROR,
            data={"sync_mode": task.sync_mode}
        )

    # 应用更新
    update_data = request.model_dump(exclude_unset=True)

    if 'description' in update_data:
        task.description = update_data['description']

    if 'timeout_seconds' in update_data:
        task.timeout_seconds = update_data['timeout_seconds']

    if 'schedule_expression' in update_data:
        old_schedule_expression = task.schedule_expression
        task.schedule_expression = update_data['schedule_expression']
        # 如果调度表达式发生变化，需要重新调度任务
        if old_schedule_expression != task.schedule_expression:
            from app.module.collection.schedule import reschedule_collection_task
            reschedule_collection_task(task_id, task.schedule_expression)

    if 'config' in update_data:
        # 重新生成任务配置文件
        template = await db.execute(select(CollectionTemplate).where(CollectionTemplate.id == task.template_id))
        template = template.scalar_one_or_none()
        if template:
            DataxClient.generate_datx_config(request.config, template, task.target_path)
            task.config = json.dumps(request.config.dict())

    # 如果任务处于 FAILED 状态，修改后重置为 PENDING，允许重新执行
    if task.status == TaskStatus.FAILED.name:
        task.status = TaskStatus.PENDING.name

    await db.commit()
    await db.refresh(task)

    return SuccessResponse(
        data=converter_to_response(task)
    )


@router.delete("", response_model=StandardResponse[str], status_code=200)
async def delete_collection_tasks(
    ids: list[str] = Query(..., description="List of task IDs to delete"),
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
    # 检查任务是否存在
    task_id = ids[0]
    task = await db.get(CollectionTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.COLLECTION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 删除任务执行记录（在事务内）
    async with transaction(db):
        await db.execute(
            TaskExecution.__table__.delete()
            .where(TaskExecution.task_id == task_id)
        )

        # 删除任务
        await db.delete(task)

    # 事务提交后，先转换硬链接，再删除文件系统和调度
    logger.info(f"Converting hard links before deleting task {task_id}")
    await convert_dataset_hardlinks_before_delete(task_id, db)

    remove_collection_task(task_id)

    target_path = f"/dataset/local/{task_id}"
    if os.path.exists(target_path):
        shutil.rmtree(target_path)
    job_path = f"/flow/data-collection/{task_id}"
    if os.path.exists(job_path):
        shutil.rmtree(job_path)

    return SuccessResponse(
        data="success"
    )

@router.get("/{task_id}", response_model=StandardResponse[CollectionTaskBase])
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取归集任务详情"""
    # 根据ID查询任务
    task = await db.get(CollectionTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.COLLECTION_TASK_NOT_FOUND, data={"task_id": task_id})

    return SuccessResponse(data=converter_to_response(task))
