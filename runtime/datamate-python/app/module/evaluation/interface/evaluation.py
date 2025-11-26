import uuid
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import ValidationError

from app.core.logging import get_logger
from app.db.session import get_db
from app.db.models import EvaluationTask as EvaluationTaskModel, EvaluationItem as EvaluationItemModel
from app.module.evaluation.schema.evaluation import (
    CreateEvaluationTaskRequest,
    PagedEvaluationTaskResponse,
    EvaluationTaskDetailResponse
)
from app.module.shared.schema.common import StandardResponse, TaskStatus

router = APIRouter(
    prefix="/tasks",
    tags=["evaluation/tasks"],
)

logger = get_logger(__name__)


@router.post("", response_model=StandardResponse[EvaluationTaskDetailResponse], status_code=201)
async def create_evaluation_task(
    request: CreateEvaluationTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    创建评估任务

    Args:
        request: 创建评估任务请求
        db: 数据库会话

    Returns:
        StandardResponse[EvaluationTaskDetailResponse]: 创建的任务详情
    """
    try:
        # 检查任务名称是否已存在
        existing_task = await db.execute(
            select(EvaluationTaskModel).where(EvaluationTaskModel.name == request.name)
        )
        if existing_task.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Evaluation task with name '{request.name}' already exists")

        # 创建评估任务
        task = EvaluationTaskModel(
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
                "modelName": request.eval_config.model_name,
                "baseUrl": request.eval_config.base_url
            }),
            status=TaskStatus.PENDING.value,
            eval_process=0.0,
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        # 转换响应模型
        response = _map_to_task_detail_response(task)
        return StandardResponse(
            code=200,
            message="Evaluation task created successfully",
            data=response
        )

    except ValidationError as e:
        await db.rollback()
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create evaluation task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=StandardResponse[PagedEvaluationTaskResponse])
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
    try:
        # 构建查询条件
        query = select(EvaluationTaskModel)

        if name:
            query = query.where(EvaluationTaskModel.name.ilike(f"%{name}%"))
        if status:
            query = query.where(EvaluationTaskModel.status == status)
        if task_type:
            query = query.where(EvaluationTaskModel.task_type == task_type)

        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        # 分页查询
        offset = (page - 1) * size
        tasks = (await db.execute(
            query.order_by(EvaluationTaskModel.created_at.desc())
                 .offset(offset)
                 .limit(size)
        )).scalars().all()

        # 转换为响应模型
        items = [_map_to_task_detail_response(task) for task in tasks]
        total_pages = (total + size - 1) // size if size > 0 else 0

        return StandardResponse(
            code=200,
            message="Success",
            data=PagedEvaluationTaskResponse(
                content=items,
                totalElements=total,
                totalPages=total_pages,
                page=page,
                size=size,
            )
        )

    except Exception as e:
        logger.error(f"Failed to list evaluation tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{task_id}", response_model=StandardResponse[EvaluationTaskDetailResponse])
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
    try:
        task = await db.get(EvaluationTaskModel, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Evaluation task not found")

        # 获取评估项
        items_query = select(EvaluationItemModel).where(EvaluationItemModel.task_id == task_id)
        items = (await db.execute(items_query)).scalars().all()

        # 转换为响应模型
        response = _map_to_task_detail_response(task, items)
        return StandardResponse(
            code=200,
            message="Success",
            data=response
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get evaluation task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("", response_model=StandardResponse[str], status_code=200)
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
        StandardResponse[None]: 删除结果
    """
    try:
        # 检查任务是否存在
        task_id = ids[0]
        task = await db.get(EvaluationTaskModel, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Evaluation task not found")

        # 删除评估项
        await db.execute(
            EvaluationItemModel.__table__.delete()
            .where(EvaluationItemModel.task_id == task_id)
        )

        # 删除任务
        await db.delete(task)
        await db.commit()

        return StandardResponse(
            code=200,
            message="Evaluation task deleted successfully",
            data="success"
        )

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete evaluation task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _map_to_task_detail_response(
    task: EvaluationTaskModel,
    items: Optional[List[EvaluationItemModel]] = None
) -> EvaluationTaskDetailResponse:
    """将数据库模型转换为任务详情响应模型"""
    return EvaluationTaskDetailResponse(
        id=task.id,
        name=task.name,
        description=task.description,
        taskType=task.task_type,
        sourceType=task.source_type,
        sourceId=task.source_id,
        sourceName=task.source_name,
        status=task.status,
        evalProcess=task.eval_process,
        evalPrompt=task.eval_prompt,
        evalConfig=json.loads(task.eval_config),
        createdAt=task.created_at.isoformat() if task.created_at else None,
        updatedAt=task.updated_at.isoformat() if task.updated_at else None,
    )
