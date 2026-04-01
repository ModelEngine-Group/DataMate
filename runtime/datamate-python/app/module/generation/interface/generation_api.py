"""
数据合成模块 API 接口层

该模块提供数据合成任务的 RESTful API 接口。
每个接口负责：参数解析 → 调用服务 → 返回响应
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessError, ErrorCodes, SuccessResponse
from app.core.logging import get_logger
from app.db.session import get_db
from app.module.generation.schema.generation import (
    CreateSynthesisTaskRequest,
    DataSynthesisTaskItem,
    PagedDataSynthesisTaskResponse,
    SynthesisType,
    PagedDataSynthesisFileTaskResponse,
    PagedDataSynthesisChunkResponse,
    SynthesisDataItem,
    SynthesisDataUpdateRequest,
    BatchDeleteSynthesisDataRequest,
    BatchDeleteChunkInstancesRequest,
    BatchDeleteChunkInstancesByFileRequest,
    BatchDeleteChunkInstancesByTaskRequest,
    SynthesisDataPatchItem,
    ExportSynthesisDataRequest,
    ExportSynthesisDataResponse,
)
from app.module.generation.service.chunk_query_service import ChunkQueryService
from app.module.generation.service.export_service import SynthesisDatasetExporter, SynthesisExportError
from app.module.generation.service.file_query_service import FileQueryService
from app.module.generation.service.generation_service import GenerationService
from app.module.generation.service.prompt import get_prompt
from app.module.generation.service.synthesis_data_query_service import SynthesisDataQueryService
from app.module.generation.service.task_create_service import TaskCreateService
from app.module.generation.service.task_delete_service import TaskDeleteService
from app.module.generation.service.task_query_service import TaskQueryService
from app.module.generation.service.task_executor import execute_generation_task
from app.module.shared.schema import StandardResponse

router = APIRouter(
    prefix="/gen",
    tags=["gen"]
)

logger = get_logger(__name__)


# ==================== 任务接口 ====================

@router.post("/task", response_model=StandardResponse[DataSynthesisTaskItem])
async def create_synthesis_task(
    request: CreateSynthesisTaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    创建数据合成任务

    使用改进的后台任务执行器，将任务提交到独立的线程池中执行，
    避免阻塞主事件循环，确保前端接口的响应性。

    Args:
        request: 创建任务请求
        background_tasks: 后台任务
        db: 数据库会话

    Returns:
        创建的任务
    """
    create_service = TaskCreateService(db)
    task = await create_service.create(request)

    # 使用新的执行器提交任务到线程池
    # 这样可以真正隔离后台任务，避免阻塞主事件循环
    async def run_task_in_executor(task_id: str):
        """在线程池中执行任务"""
        # 定义一个包装函数来正确调用process_task
        async def process_task_wrapper(tid: str):
            # 创建新的GenerationService实例，使用独立的会话
            from app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                service = GenerationService(session)
                await service.process_task(tid)

        await execute_generation_task(task_id, process_task_wrapper)

    background_tasks.add_task(run_task_in_executor, task.id)
    logger.info(f"Submitted generation task {task.id} to background executor")

    return SuccessResponse(data=DataSynthesisTaskItem.from_orm_with_config(task))


@router.get("/task/{task_id}", response_model=StandardResponse[DataSynthesisTaskItem])
async def get_synthesis_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    获取数据合成任务详情

    Args:
        task_id: 任务 ID
        db: 数据库会话

    Returns:
        任务详情
    """
    query_service = TaskQueryService(db)
    task = await query_service.get_task(task_id)
    if not task:
        raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND, data={"task_id": task_id})
    return SuccessResponse(data=DataSynthesisTaskItem.from_orm_with_config(task))


@router.get("/tasks", response_model=StandardResponse[PagedDataSynthesisTaskResponse])
async def list_synthesis_tasks(
    page: int = 1,
    page_size: int = 10,
    synthesis_type: str | None = None,
    status: str | None = None,
    name: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """
    分页列出所有数据合成任务

    Args:
        page: 页码
        page_size: 每页数量
        synthesis_type: 合成类型过滤
        status: 状态过滤
        name: 名称模糊搜索
        db: 数据库会话

    Returns:
        分页任务列表
    """
    query_service = TaskQueryService(db)
    result = await query_service.list_tasks(
        page=page,
        page_size=page_size,
        synthesis_type=synthesis_type,
        status=status,
        name=name,
    )
    return SuccessResponse(data=result)


@router.delete("/task/{task_id}", response_model=StandardResponse)
async def delete_synthesis_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除数据合成任务

    Args:
        task_id: 任务 ID
        db: 数据库会话
    """
    delete_service = TaskDeleteService(db)
    await delete_service.delete_task(task_id)
    return SuccessResponse(data=None)


@router.delete("/task/{task_id}/{file_id}", response_model=StandardResponse)
async def delete_synthesis_file_task(
    task_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除数据合成任务中的文件任务

    Args:
        task_id: 任务 ID
        file_id: 文件任务 ID
        db: 数据库会话
    """
    delete_service = TaskDeleteService(db)
    await delete_service.delete_file_task(task_id, file_id)
    return SuccessResponse(data=None)


# ==================== 提示词接口 ====================

@router.get("/prompt", response_model=StandardResponse[str])
async def get_prompt_by_type(synth_type: SynthesisType):
    """
    获取提示词

    Args:
        synth_type: 合成类型

    Returns:
        提示词内容
    """
    prompt = get_prompt(synth_type)
    return SuccessResponse(data=prompt)


# ==================== 文件任务接口 ====================

@router.get(
    "/task/{task_id}/files",
    response_model=StandardResponse[PagedDataSynthesisFileTaskResponse]
)
async def list_synthesis_file_tasks(
    task_id: str,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    分页获取任务下的文件任务列表

    Args:
        task_id: 任务 ID
        page: 页码
        page_size: 每页数量
        db: 数据库会话

    Returns:
        分页文件任务列表
    """
    query_service = TaskQueryService(db)
    task = await query_service.get_task(task_id)
    if not task:
        raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND, data={"task_id": task_id})

    file_query = FileQueryService(db)
    items, total = await file_query.list_by_task(task_id, page, page_size)

    return SuccessResponse(data=PagedDataSynthesisFileTaskResponse(
        content=items,
        totalElements=total,
        totalPages=(total + page_size - 1) // page_size,
        page=page,
        size=page_size,
    ))


# ==================== 切片接口 ====================

@router.get(
    "/file/{file_id}/chunks",
    response_model=StandardResponse[PagedDataSynthesisChunkResponse]
)
async def list_chunks_by_file(
    file_id: str,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    根据文件任务 ID 分页查询切片列表

    Args:
        file_id: 文件任务 ID
        page: 页码
        page_size: 每页数量
        db: 数据库会话

    Returns:
        分页切片列表
    """
    file_query = FileQueryService(db)
    file_task = await file_query.get_by_id(file_id)
    if not file_task:
        raise BusinessError(ErrorCodes.GENERATION_FILE_NOT_FOUND, data={"file_id": file_id})

    chunk_query = ChunkQueryService(db)
    items, total = await chunk_query.list_by_file(file_id, page, page_size)

    return SuccessResponse(data=PagedDataSynthesisChunkResponse(
        content=items,
        totalElements=total,
        totalPages=(total + page_size - 1) // page_size,
        page=page,
        size=page_size,
    ))


@router.get(
    "/chunk/{chunk_id}/data",
    response_model=StandardResponse[List[SynthesisDataItem]]
)
async def list_synthesis_data_by_chunk(chunk_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据切片 ID 查询所有合成结果数据

    Args:
        chunk_id: 切片 ID
        db: 数据库会话

    Returns:
        合成数据列表
    """
    chunk_query = ChunkQueryService(db)
    chunk = await chunk_query.get_by_id(chunk_id)
    if not chunk:
        raise BusinessError(ErrorCodes.GENERATION_CHUNK_NOT_FOUND, data={"chunk_id": chunk_id})

    data_query = SynthesisDataQueryService(db)
    items = await data_query.list_by_chunk(chunk_id)
    return SuccessResponse(data=items)


# ==================== 导出接口 ====================

@router.post(
    "/task/{task_id}/export-dataset/{dataset_id}",
    response_model=StandardResponse[str]
)
async def export_synthesis_task_to_dataset(
    task_id: str,
    dataset_id: str,
    format: str = "alpaca",
    db: AsyncSession = Depends(get_db),
):
    """
    将合成任务的数据归档到已有数据集

    Args:
        task_id: 任务 ID
        dataset_id: 目标数据集 ID
        format: 导出格式
        db: 数据库会话

    Returns:
        数据集 ID
    """
    exporter = SynthesisDatasetExporter(db, format=format)
    generation = GenerationService(db)
    try:
        dataset = await exporter.export_task_to_dataset(task_id, dataset_id)
        await generation.add_synthesis_to_graph(db, task_id, dataset_id)
    except SynthesisExportError as e:
        logger.error(
            "Failed to export synthesis task %s to dataset %s: %s",
            task_id, dataset_id, e
        )
        raise BusinessError(ErrorCodes.OPERATION_FAILED, data={"error": str(e)})

    return SuccessResponse(data=dataset.id)


@router.post(
    "/data/export",
    response_model=StandardResponse[ExportSynthesisDataResponse],
)
async def export_synthesis_data(
    request: ExportSynthesisDataRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    将合成数据导出为指定格式的 JSONL 文件

    Args:
        request: 导出请求
        db: 数据库会话

    Returns:
        导出结果
    """
    exporter = SynthesisDatasetExporter(
        db,
        format=request.format.value,
        output_path=request.output_path,
    )
    result = await exporter.export_data(
        task_id=request.task_id,
        file_instance_ids=request.file_instance_ids,
    )
    return SuccessResponse(data=result)


# ==================== 删除接口 ====================

@router.delete("/chunk/{chunk_id}", response_model=StandardResponse)
async def delete_chunk_with_data(chunk_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除切片及其关联的合成数据

    Args:
        chunk_id: 切片 ID
        db: 数据库会话
    """
    delete_service = TaskDeleteService(db)
    await delete_service.delete_chunk(chunk_id)
    return SuccessResponse(data=None)


@router.delete("/chunk/{chunk_id}/data", response_model=StandardResponse)
async def delete_synthesis_data_by_chunk(chunk_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除切片下的所有合成数据

    Args:
        chunk_id: 切片 ID
        db: 数据库会话

    Returns:
        删除的记录数
    """
    delete_service = TaskDeleteService(db)
    deleted = await delete_service.delete_synthesis_data_by_chunk(chunk_id)
    return SuccessResponse(data=deleted)


@router.delete("/data/batch", response_model=StandardResponse)
async def batch_delete_synthesis_data(
    request: BatchDeleteSynthesisDataRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    批量删除合成数据

    Args:
        request: 批量删除请求
        db: 数据库会话

    Returns:
        删除的记录数
    """
    delete_service = TaskDeleteService(db)
    deleted = await delete_service.batch_delete_synthesis_data(request.ids)
    return SuccessResponse(data=deleted)


@router.patch("/data/{data_id}", response_model=StandardResponse)
async def update_synthesis_data_field(
    data_id: str,
    body: SynthesisDataUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    修改合成数据

    Args:
        data_id: 数据 ID
        body: 更新请求
        db: 数据库会话

    Returns:
        更新后的数据
    """
    data_query = SynthesisDataQueryService(db)
    record = await data_query.update(data_id, body.data)
    if not record:
        raise BusinessError(ErrorCodes.GENERATION_DATA_NOT_FOUND, data={"data_id": data_id})
    return SuccessResponse(data=record)


@router.post(
    "/batch-delete/chunks",
    response_model=StandardResponse,
)
async def batch_delete_chunk_instances(
    request: BatchDeleteChunkInstancesRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    批量删除切片

    Args:
        request: 批量删除请求
        db: 数据库会话
    """
    delete_service = TaskDeleteService(db)
    await delete_service.batch_delete_chunks(request.chunk_ids)
    return SuccessResponse(data=None)


@router.post(
    "/batch-delete/chunks-by-file",
    response_model=StandardResponse,
)
async def batch_delete_chunk_instances_by_file(
    request: BatchDeleteChunkInstancesByFileRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    按文件任务维度删除切片

    Args:
        request: 删除请求
        db: 数据库会话
    """
    file_query = FileQueryService(db)
    file_task = await file_query.get_by_id(request.file_id)
    if not file_task:
        raise BusinessError(ErrorCodes.GENERATION_FILE_NOT_FOUND)

    delete_service = TaskDeleteService(db)
    await delete_service.delete_chunks_by_file(request.file_id)
    return SuccessResponse(data=None)


@router.post(
    "/batch-delete/chunks-by-task",
    response_model=StandardResponse,
)
async def batch_delete_chunk_instances_by_task(
    request: BatchDeleteChunkInstancesByTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    按任务维度删除切片

    Args:
        request: 删除请求
        db: 数据库会话
    """
    query_service = TaskQueryService(db)
    task = await query_service.get_task(request.task_id)
    if not task:
        raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND)

    delete_service = TaskDeleteService(db)
    await delete_service.delete_chunks_by_task(request.task_id)
    return SuccessResponse(data=None)


# ==================== 批量查询接口 ====================

@router.post(
    "/data/patch",
    response_model=StandardResponse[List[SynthesisDataPatchItem]],
)
async def get_synthesis_data_patch(
    task_id: Optional[str] = None,
    file_instance_id: Optional[str] = None,
    chunk_instance_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    批量查询合成数据

    Args:
        task_id: 任务 ID
        file_instance_id: 文件任务 ID
        chunk_instance_id: 切片 ID
        db: 数据库会话

    Returns:
        合成数据列表
    """
    data_query = SynthesisDataQueryService(db)

    if chunk_instance_id:
        items = await data_query.list_by_chunk(chunk_instance_id)
        return SuccessResponse(data=[SynthesisDataPatchItem.model_validate(item) for item in items])

    if file_instance_id:
        file_query = FileQueryService(db)
        file_task = await file_query.get_by_id(file_instance_id)
        if not file_task:
            raise BusinessError(ErrorCodes.GENERATION_FILE_NOT_FOUND)
        items = await data_query.list_by_file(file_instance_id)
        return SuccessResponse(data=items)

    if task_id:
        query_service = TaskQueryService(db)
        task = await query_service.get_task(task_id)
        if not task:
            raise BusinessError(ErrorCodes.GENERATION_TASK_NOT_FOUND)
        items = await data_query.list_by_task(task_id)
        return SuccessResponse(data=items)

    return SuccessResponse(data=[])
