from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.session import get_db
from app.module.cleaning.schema import (
    CleaningTaskDto,
    CreateCleaningTaskRequest,
    CleaningResultDto,
    CleaningTaskLog,
)
from app.module.cleaning.service import CleaningTaskService
from app.module.shared.schema import StandardResponse, PaginatedData

logger = get_logger(__name__)

router = APIRouter(prefix="/cleaning/tasks", tags=["Cleaning Tasks"])


def _get_operator_service():
    """Get operator service"""
    from app.module.operator.service import OperatorService
    from app.module.operator.repository import (
        OperatorRepository,
        CategoryRelationRepository,
        OperatorReleaseRepository,
    )
    from app.module.operator.parsers import ParserHolder
    from app.module.shared.file_service import FileService
    from app.module.shared.chunk_upload_repository import ChunkUploadRepository

    return OperatorService(
        operator_repo=OperatorRepository(None),
        category_relation_repo=CategoryRelationRepository(None),
        operator_release_repo=OperatorReleaseRepository(None),
        parser_holder=ParserHolder(),
        file_service=FileService(ChunkUploadRepository()),
    )


def _get_task_service(db: AsyncSession) -> CleaningTaskService:
    """Get cleaning task service instance"""
    from app.module.cleaning.service import (
        CleaningTaskScheduler,
        CleaningTaskValidator,
    )
    from app.module.cleaning.repository import (
        CleaningTaskRepository,
        CleaningResultRepository,
        OperatorInstanceRepository,
    )
    from app.module.cleaning.runtime_client import RuntimeClient
    from app.module.dataset.service import DatasetManagementService
    from app.module.shared.common.lineage import LineageService

    runtime_client = RuntimeClient()
    scheduler = CleaningTaskScheduler(
        task_repo=CleaningTaskRepository(None),
        runtime_client=runtime_client
    )
    operator_service = _get_operator_service()
    dataset_service = DatasetManagementService(db)
    lineage_service = LineageService(db)

    task_repo = CleaningTaskRepository(None)

    return CleaningTaskService(
        task_repo=task_repo,
        result_repo=CleaningResultRepository(None),
        operator_instance_repo=OperatorInstanceRepository(None),
        operator_service=operator_service,
        scheduler=scheduler,
        validator=CleaningTaskValidator(task_repo=task_repo, template_repo=None),
        dataset_service=dataset_service,
        lineage_service=lineage_service,
    )


@router.get(
    "",
    response_model=StandardResponse[PaginatedData[CleaningTaskDto]],
    summary="查询清洗任务列表",
    description="根据参数查询清洗任务列表（支持分页、状态过滤、关键词搜索）",
    tags=['mcp']
)
async def get_cleaning_tasks(
    page: int = 0,
    size: int = 10,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Query cleaning tasks"""
    task_service = _get_task_service(db)

    tasks = await task_service.get_tasks(db, status, keyword, page, size)
    count = await task_service.count_tasks(db, status, keyword)
    total_pages = (count + size - 1) // size if size > 0 else 0

    return StandardResponse(
        code="0",
        message="success",
        data=PaginatedData(
            page=page,
            size=size,
            total_elements=count,
            total_pages=total_pages,
            content=tasks,
        )
    )


@router.post(
    "",
    response_model=StandardResponse[CleaningTaskDto],
    summary="创建清洗任务",
    description="根据模板ID或算子列表创建清洗任务",
    tags=['mcp']
)
async def create_cleaning_task(
    request: CreateCleaningTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create cleaning task"""
    task_service = _get_task_service(db)

    task = await task_service.create_task(db, request)
    await db.commit()

    await task_service.execute_task(db, task.id)
    await db.commit()

    return StandardResponse(code="0", message="success", data=task)


@router.get(
    "/{task_id}",
    response_model=StandardResponse[CleaningTaskDto],
    summary="获取清洗任务详情",
    description="根据ID获取清洗任务详细信息"
)
async def get_cleaning_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get cleaning task by ID"""
    task_service = _get_task_service(db)
    task = await task_service.get_task(db, task_id)
    return StandardResponse(code="0", message="success", data=task)


@router.delete(
    "/{task_id}",
    response_model=StandardResponse[str],
    summary="删除清洗任务",
    description="删除指定的清洗任务"
)
async def delete_cleaning_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete cleaning task"""
    task_service = _get_task_service(db)
    await task_service.delete_task(db, task_id)
    await db.commit()
    return StandardResponse(code="0", message="success", data=task_id)


@router.post(
    "/{task_id}/stop",
    response_model=StandardResponse[str],
    summary="停止清洗任务",
    description="停止正在运行的清洗任务"
)
async def stop_cleaning_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stop cleaning task"""
    task_service = _get_task_service(db)
    await task_service.stop_task(db, task_id)
    await db.commit()
    return StandardResponse(code="0", message="success", data=task_id)


@router.post(
    "/{task_id}/execute",
    response_model=StandardResponse[str],
    summary="执行清洗任务",
    description="重新执行清洗任务"
)
async def execute_cleaning_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Execute cleaning task"""
    task_service = _get_task_service(db)
    await task_service.execute_task(db, task_id)
    await db.commit()
    return StandardResponse(code="0", message="success", data=task_id)


@router.get(
    "/{task_id}/result",
    response_model=StandardResponse[list[CleaningResultDto]],
    summary="获取清洗任务结果",
    description="获取指定清洗任务的执行结果"
)
async def get_cleaning_task_results(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get cleaning task results"""
    task_service = _get_task_service(db)
    results = await task_service.get_task_results(db, task_id)
    return StandardResponse(code="0", message="success", data=results)


@router.get(
    "/{task_id}/log/{retry_count}",
    response_model=StandardResponse[list[CleaningTaskLog]],
    summary="获取清洗任务日志",
    description="获取指定清洗任务的执行日志"
)
async def get_cleaning_task_log(
    task_id: str,
    retry_count: int,
    db: AsyncSession = Depends(get_db),
):
    """Get cleaning task log"""
    task_service = _get_task_service(db)
    logs = await task_service.get_task_log(db, task_id, retry_count)
    return StandardResponse(code="0", message="success", data=logs)
