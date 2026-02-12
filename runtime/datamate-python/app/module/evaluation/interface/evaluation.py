import asyncio
import uuid
import math
import json
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.logging import get_logger
from app.core.exception import ErrorCodes, BusinessError, SuccessResponse
from app.db.models.data_evaluation import EvaluationFile
from app.db.session import get_db
from app.db.models import EvaluationTask, EvaluationItem, DatasetFiles
from app.module.evaluation.schema.evaluation import (
    CreateEvaluationTaskRequest,
    PagedEvaluationTaskResponse,
    EvaluationTaskDetailResponse,
    PagedEvaluationItemsResponse,
    EvaluationItemResponse, PagedEvaluationFilesResponse, EvaluationFileResponse
)
from app.module.evaluation.schema.prompt import get_prompt
from app.module.evaluation.schema.prompt_template import PromptTemplateResponse
from app.module.evaluation.service.prompt_template_service import PromptTemplateService
from app.module.evaluation.service.evaluation import EvaluationTaskService
from app.module.shared.schema.common import StandardResponse, TaskStatus
from app.module.system.service.common_service import get_model_by_id

router = APIRouter(
    prefix="",
    tags=["evaluation"],
)

logger = get_logger(__name__)


@router.get("/prompt-templates", response_model=StandardResponse[PromptTemplateResponse])
async def get_prompt_templates():
    """
    获取所有可用的评估提示模板

    Returns:
        StandardResponse with list of prompt templates
    """
    templates = PromptTemplateService.get_prompt_templates()
    return SuccessResponse(data=templates)


@router.post("/tasks", response_model=StandardResponse[EvaluationTaskDetailResponse])
async def create_evaluation_task(
    request: CreateEvaluationTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    创建评估任务

    Args:
        request: 创建评估任务请求
        db: 数据库会话

    Returns:
        StandardResponse[EvaluationTaskDetailResponse]: 创建的任务详情
    """
    # 检查任务名称是否已存在
    existing_task = await db.execute(
        select(EvaluationTask).where(EvaluationTask.name == request.name)
    )
    if existing_task.scalar_one_or_none():
        raise BusinessError(ErrorCodes.EVALUATION_MODEL_NOT_FOUND, data={"name": request.name})

    models = await get_model_by_id(db, request.eval_config.model_id)
    if not models:
        raise BusinessError(ErrorCodes.EVALUATION_MODEL_NOT_FOUND, data={"model_id": request.eval_config.model_id})

    # 创建评估任务
    task = EvaluationTask(
        id=str(uuid.uuid4()),
        name=request.name,
        description=request.description,
        task_type=request.task_type,
        source_type=request.source_type,
        source_id=request.source_id,
        source_name=request.source_name,
        eval_prompt=request.eval_prompt,
        eval_config=json.dumps({
            "modelId": request.eval_config.model_id,
            "modelName": models.model_name,
            "dimensions": request.eval_config.dimensions,
        }),
        status=TaskStatus.PENDING.value,
        eval_process=0.0,
    )

    db.add(task)
    # Commit first to persist the task before scheduling background work
    await db.commit()
    # Schedule background execution without blocking the current request
    asyncio.create_task(EvaluationTaskService.run_evaluation_task(task.id))

    # Refresh the task to return latest state
    await db.refresh(task)

    # 转换响应模型
    response = _map_to_task_detail_response(task)
    return SuccessResponse(
        data=response,
        message="Evaluation task created successfully"
    )


@router.get("/tasks", response_model=StandardResponse[PagedEvaluationTaskResponse])
async def list_evaluation_tasks(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="任务名称模糊查询"),
    status: Optional[str] = Query(None, description="任务状态过滤"),
    task_type: Optional[str] = Query(None, description="任务类型过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询评估任务

    Args:
        page: 页码，从1开始
        size: 每页数量
        name: 任务名称模糊查询
        status: 任务状态过滤
        task_type: 任务类型过滤
        db: 数据库会话

    Returns:
        StandardResponse[PagedEvaluationTaskResponse]: 分页的评估任务列表
    """
    # 构建查询条件
    query = select(EvaluationTask)

    if name:
        query = query.where(EvaluationTask.name.ilike(f"%{name}%"))
    if status:
        query = query.where(EvaluationTask.status == status)
    if task_type:
        query = query.where(EvaluationTask.task_type == task_type)

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # 分页查询
    offset = (page - 1) * size
    tasks = (await db.execute(
        query.order_by(EvaluationTask.created_at.desc())
             .offset(offset)
             .limit(size)
    )).scalars().all()

    # 转换为响应模型
    items = [_map_to_task_detail_response(task) for task in tasks]
    total_pages = math.ceil(total / size) if total > 0 else 0

    return SuccessResponse(
        data=PagedEvaluationTaskResponse(
            content=items,
            totalElements=total,
            totalPages=total_pages,
            page=page,
            size=size,
        )
    )

@router.get("/tasks/{task_id}/files", response_model=StandardResponse[PagedEvaluationFilesResponse])
async def list_evaluation_files(
    task_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询评估文件

    Args:
        task_id: 评估任务ID
        page: 页码，从1开始
        size: 每页数量
        db: 数据库会话

    Returns:
        StandardResponse[PagedEvaluationFilesResponse]: 分页的评估文件列表
    """
    task = await db.get(EvaluationTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.EVALUATION_TASK_NOT_FOUND, data={"task_id": task_id})

    offset = (page - 1) * size
    query = select(EvaluationFile).where(EvaluationFile.task_id == task_id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    files = (await db.execute(query.offset(offset).limit(size))).scalars().all()
    total_pages = math.ceil(total / size) if total > 0 else 0
    file_responses = [
        EvaluationFileResponse(
            taskId=file.task_id,
            fileId=file.file_id,
            fileName=file.file_name,
            totalCount=file.total_count,
            evaluatedCount=file.evaluated_count,
            pendingCount=file.total_count - file.evaluated_count
        )
        for file in files
    ]
    return SuccessResponse(
        data=PagedEvaluationFilesResponse(
            content=file_responses,
            totalElements=total,
            totalPages=total_pages,
            page=page,
            size=size,
        )
    )


@router.get("/tasks/{task_id}/items", response_model=StandardResponse[PagedEvaluationItemsResponse])
async def list_evaluation_items(
    task_id: str,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    file_id: Optional[str] = Query(None, description="文件过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询评估条目

    Args:
        task_id: 评估任务ID
        page: 页码，从1开始
        size: 每页数量
        status: 状态过滤
        file_id: 文件过滤
        db: 数据库会话

    Returns:
        StandardResponse[PagedEvaluationItemsResponse]: 分页的评估条目列表
    """
    # 检查任务是否存在
    task = await db.get(EvaluationTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.EVALUATION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 构建查询条件
    query = select(EvaluationItem).where(EvaluationItem.task_id == task_id)

    if status:
        query = query.where(EvaluationItem.status == status)

    if file_id:
        query = query.where(EvaluationItem.file_id == file_id)

    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # 分页查询
    offset = (page - 1) * size
    items = (await db.execute(query.offset(offset).limit(size))).scalars().all()

    # 转换为响应模型
    item_responses = [
        EvaluationItemResponse(
            id=item.id,
            taskId=item.task_id,
            itemId=item.item_id,
            fileId=item.file_id,
            evalContent=json.loads(item.eval_content) if item.eval_content else None,
            evalScore=float(item.eval_score) if item.eval_score else None,
            evalResult=json.loads(item.eval_result),
            status=item.status
        )
        for item in items
    ]

    total_pages = math.ceil(total / size) if total > 0 else 0

    return SuccessResponse(
        data=PagedEvaluationItemsResponse(
            content=item_responses,
            totalElements=total,
            totalPages=total_pages,
            page=page,
            size=size,
        )
    )


@router.get("/tasks/{task_id}", response_model=StandardResponse[EvaluationTaskDetailResponse])
async def get_evaluation_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取评估任务详情

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        StandardResponse[EvaluationTaskDetailResponse]: 评估任务详情
    """
    task = await db.get(EvaluationTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.EVALUATION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 转换为响应模型
    response = _map_to_task_detail_response(task)
    return SuccessResponse(data=response)


@router.delete("/tasks", response_model=StandardResponse[str], status_code=200)
async def delete_eval_tasks(
    ids: list[str] = Query(..., description="要删除的评估任务ID列表"),
    db: AsyncSession = Depends(get_db),
):
    """
    删除评估任务

    Args:
        ids: 任务ID
        db: 数据库会话

    Returns:
        StandardResponse[str]: 删除结果
    """
    # 检查任务是否存在
    task_id = ids[0]
    task = await db.get(EvaluationTask, task_id)
    if not task:
        raise BusinessError(ErrorCodes.EVALUATION_TASK_NOT_FOUND, data={"task_id": task_id})

    # 删除评估项
    await db.execute(
        EvaluationItem.__table__.delete()
        .where(EvaluationItem.task_id == task_id)
    )

    # 删除评估文件
    await db.execute(
        EvaluationFile.__table__.delete()
        .where(EvaluationFile.task_id == task_id)
    )

    # 删除任务
    await db.delete(task)
    await db.commit()

    return SuccessResponse(
        data="success",
        message="Evaluation task deleted successfully"
    )


def _map_to_task_detail_response(
    task: EvaluationTask
) -> EvaluationTaskDetailResponse:
    """将数据库模型转换为任务详情响应模型"""
    task_response = EvaluationTaskDetailResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        taskType=task.task_type,
        sourceType=task.source_type,
        sourceId=task.source_id,
        sourceName=task.source_name,
        status=task.status,
        evalMethod=task.eval_method,
        evalProcess=task.eval_process,
        evalPrompt=task.eval_prompt,
        evalConfig=json.loads(task.eval_config),
        createdAt=task.created_at.isoformat() if task.created_at else None,
        updatedAt=task.updated_at.isoformat() if task.updated_at else None,
    )
    task_response.eval_prompt = get_prompt(task_response.task_type, task_response.eval_config.get("dimensions"))
    return task_response
