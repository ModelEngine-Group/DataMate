
import math
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_collection import TaskExecution
from app.db.session import get_db
from app.module.collection.schema.collection import TaskExecutionBase, converter_execution_to_response
from app.module.shared.schema import StandardResponse, PaginatedData

router = APIRouter(
    prefix="/executions",
    tags=["data-collection/executions"],
)
logger = get_logger(__name__)


@router.get("", response_model=StandardResponse[PaginatedData[TaskExecutionBase]])
async def list_executions(
    page: int = 1,
    size: int = 20,
    task_id: Optional[str] = Query(None, description="任务ID"),
    task_name: Optional[str] = Query(None, description="任务名称模糊查询"),
    start_time: Optional[datetime] = Query(None, description="开始执行时间范围-起（started_at >= start_time）"),
    end_time: Optional[datetime] = Query(None, description="开始执行时间范围-止（started_at <= end_time）"),
    db: AsyncSession = Depends(get_db)
):
    """分页查询归集任务执行记录"""
    try:
        query = select(TaskExecution)

        if task_id:
            query = query.where(TaskExecution.task_id == task_id)

        if task_name:
            query = query.where(TaskExecution.task_name.ilike(f"%{task_name}%"))

        if start_time:
            query = query.where(TaskExecution.started_at >= start_time)

        if end_time:
            query = query.where(TaskExecution.started_at <= end_time)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar_one()

        offset = (page - 1) * size
        executions = (await db.execute(
            query.order_by(TaskExecution.created_at.desc())
            .offset(offset)
            .limit(size)
        )).scalars().all()

        items = [converter_execution_to_response(exe) for exe in executions]
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
        logger.error(f"Failed to list task executions: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{execution_id}/log")
async def get_execution_log(
    execution_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取执行记录对应的日志文件内容"""
    try:
        execution = await db.get(TaskExecution, execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution record not found")

        log_path = getattr(execution, "log_path", None)
        if not log_path:
            raise HTTPException(status_code=404, detail="Log path not found")

        path = Path(str(log_path))
        if not path.is_absolute():
            path = Path(os.getcwd()) / path
        path = path.resolve()

        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="Log file not found")

        filename = path.name
        headers = {
            "Content-Disposition": f'inline; filename={filename}'
        }
        return FileResponse(
            path=str(path),
            media_type="text/plain; charset=utf-8",
            filename=filename,
            headers=headers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution log: {str(e)}", e)
        raise HTTPException(status_code=500, detail="Internal server error")
