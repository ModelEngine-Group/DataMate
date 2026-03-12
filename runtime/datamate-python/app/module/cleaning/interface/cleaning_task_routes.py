from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
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
        task_repo=CleaningTaskRepository(None), runtime_client=runtime_client
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
    tags=["mcp"],
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
        ),
    )


@router.post(
    "",
    response_model=StandardResponse[CleaningTaskDto],
    summary="创建清洗任务",
    description="根据模板ID或算子列表创建清洗任务",
    tags=["mcp"],
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
    description="根据ID获取清洗任务详细信息",
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
    description="删除指定的清洗任务",
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
    description="停止正在运行的清洗任务",
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
    description="重新执行清洗任务",
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
    description="获取指定清洗任务的执行结果",
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
    "/{task_id}/result/download",
    summary="下载清洗任务结果文件压缩包",
    description="下载指定清洗任务的源文件和处理后文件压缩包",
)
async def download_cleaning_result_files(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download cleaning task result files (both src and dest)"""
    import zipfile
    import io
    from pathlib import Path
    from fastapi.responses import StreamingResponse
    from app.core.exception import BusinessError, ErrorCodes

    task_service = _get_task_service(db)

    task = await task_service.get_task(db, task_id)

    results = await task_service.get_task_results(db, task_id)
    if not results:
        raise BusinessError(ErrorCodes.NOT_FOUND, f"Cleaning task {task_id} not found")

    src_path = Path("/dataset") / task.src_dataset_id

    dest_path = Path("/dataset") / task.dest_dataset_id

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for file_record in results:
            if file_record.src_name:
                src_path = src_path / file_record.src_name
                if src_path.exists():
                    zipf.write(src_path, arcname=f"src/{file_record.src_name}")

            if file_record.dest_name:
                dest_path = dest_path / file_record.dest_name
                if dest_path.exists():
                    zipf.write(dest_path, arcname=f"dest/{file_record.dest_name}")

    zip_buffer.seek(0)

    filename = f"task_{task_id}_{file_record.src_name}.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{task_id}/log/stream",
    summary="流式获取清洗任务日志",
    description="通过SSE流式获取清洗任务日志",
)
async def stream_cleaning_task_log(
    task_id: str,
    retry_count: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """Stream cleaning task log via SSE"""
    import asyncio
    import json
    import re
    from pathlib import Path

    FLOW_PATH = "/flow"

    task_service = _get_task_service(db)
    task = await task_service.task_repo.find_task_by_id(db, task_id)

    if not task:

        async def error_generator():
            yield f"data: {json.dumps({'level': 'ERROR', 'message': 'Task not found'}, ensure_ascii=False)}\n\n"

        return StreamingResponse(error_generator(), media_type="text/event-stream")

    log_path = Path(f"{FLOW_PATH}/{task_id}/output.log")
    if retry_count > 0:
        log_path = Path(f"{FLOW_PATH}/{task_id}/output.log.{retry_count}")

    standard_level_pattern = re.compile(
        r"\b(DEBUG|Debug|INFO|Info|WARN|Warn|WARNING|Warning|ERROR|Error|FATAL|Fatal)\b"
    )
    exception_suffix_pattern = re.compile(r"\b\w+(Warning|Error|Exception)\b")

    def get_log_level(line: str, default_level: str) -> str:
        if not line or not line.strip():
            return default_level
        std_match = standard_level_pattern.search(line)
        if std_match:
            return std_match.group(1).upper()
        ex_match = exception_suffix_pattern.search(line)
        if ex_match:
            match = ex_match.group(1).upper()
            if match == "WARNING":
                return "WARN"
            if match in ["ERROR", "EXCEPTION"]:
                return "ERROR"
        return default_level

    async def log_generator():
        last_position = 0
        last_level = "INFO"
        heartbeat_counter = 0
        HEARTBEAT_INTERVAL = 10

        while True:
            try:
                current_task = await task_service.task_repo.find_task_by_id(db, task_id)
                is_task_finished = current_task and current_task.status in [
                    "COMPLETED",
                    "FAILED",
                    "STOPPED",
                ]

                if log_path.exists():
                    with open(log_path, "r", encoding="utf-8") as f:
                        f.seek(last_position)
                        new_content = f.read()
                        if new_content:
                            for line in new_content.splitlines(keepends=True):
                                last_level = get_log_level(line, last_level)
                                log_entry = json.dumps(
                                    {"level": last_level, "message": line.rstrip()},
                                    ensure_ascii=False,
                                )
                                yield f"data: {log_entry}\n\n"
                            last_position = f.tell()
                            heartbeat_counter = 0
                        else:
                            heartbeat_counter += 1

                        f.seek(0, 2)
                        current_size = f.tell()
                        if current_size < last_position:
                            last_position = 0
                else:
                    heartbeat_counter += 1

                if is_task_finished:
                    yield f"data: {json.dumps({'level': 'INFO', 'message': '[END_OF_STREAM]'}, ensure_ascii=False)}\n\n"
                    break

                if heartbeat_counter >= HEARTBEAT_INTERVAL:
                    yield f"data: {json.dumps({'level': 'DEBUG', 'message': '[HEARTBEAT]'}, ensure_ascii=False)}\n\n"
                    heartbeat_counter = 0

                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                await asyncio.sleep(2)

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{task_id}/log/{retry_count}",
    response_model=StandardResponse[list[CleaningTaskLog]],
    summary="获取清洗任务日志",
    description="获取指定清洗任务的执行日志",
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


@router.get(
    "/{task_id}/log/{retry_count}/download",
    summary="下载清洗任务日志文件",
    description="下载指定清洗任务的日志文件",
)
async def download_cleaning_task_log(
    task_id: str,
    retry_count: int,
    db: AsyncSession = Depends(get_db),
):
    """Download cleaning task log file"""
    from pathlib import Path
    from fastapi.responses import FileResponse

    FLOW_PATH = "/flow"

    task_service = _get_task_service(db)
    task = await task_service.task_repo.find_task_by_id(db, task_id)

    if not task:
        from app.core.exception import BusinessError, ErrorCodes

        raise BusinessError(ErrorCodes.CLEANING_TASK_NOT_FOUND, task_id)

    log_path = Path(f"{FLOW_PATH}/{task_id}/output.log")
    if retry_count > 0:
        log_path = Path(f"{FLOW_PATH}/{task_id}/output.log.{retry_count}")

    if not log_path.exists():
        from app.core.exception import BusinessError, ErrorCodes

        raise BusinessError(
            ErrorCodes.CLEANING_TASK_LOG_NOT_FOUND,
            f"Log file not found for task {task_id}, retry {retry_count}",
        )

    # Generate filename with task name and retry count
    import re

    task_name = task.name or "未命名任务"
    safe_task_name = re.sub(
        r"[^\w\u4e00-\u9fff\-]", "_", task_name
    )  # Keep alphanumeric, Chinese, and hyphens
    run_number = retry_count + 1  # retry_count is 0-indexed, so add 1 for display
    filename = f"{safe_task_name}_第{run_number}次运行.log"

    return FileResponse(
        path=log_path,
        media_type="text/plain",
        filename=filename,
    )
