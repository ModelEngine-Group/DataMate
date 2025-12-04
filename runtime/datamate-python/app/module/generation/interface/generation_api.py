import uuid

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_synthesis import (
    save_synthesis_task,
    DataSynthesisInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles
from app.db.models.model_config import get_model_by_id
from app.db.session import get_db
from app.module.generation.schema.generation import (
    CreateSynthesisTaskRequest,
    DataSynthesisTaskItem,
    PagedDataSynthesisTaskResponse,
    SynthesisType,
    DataSynthesisFileTaskItem,
    PagedDataSynthesisFileTaskResponse,
    DataSynthesisChunkItem,
    PagedDataSynthesisChunkResponse,
    SynthesisDataItem,
)
from app.module.generation.service.generation_service import GenerationService
from app.module.generation.service.prompt import get_prompt
from app.module.shared.schema import StandardResponse

router = APIRouter(
    prefix="/gen",
    tags=["gen"]
)

logger = get_logger(__name__)

@router.post("/task", response_model=StandardResponse[DataSynthesisTaskItem])
async def create_synthesis_task(
    request: CreateSynthesisTaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """创建数据合成任务"""
    result = await get_model_by_id(db, request.model_id)
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")

    # 先根据 source_file_id 在 DatasetFiles 中查出已有文件信息
    file_ids = request.source_file_id or []
    dataset_files = []
    if file_ids:
        ds_result = await db.execute(
            select(DatasetFiles).where(DatasetFiles.id.in_(file_ids))
        )
        dataset_files = ds_result.scalars().all()

    # 保存任务到数据库
    request.source_file_id = [str(f.id) for f in dataset_files]
    synthesis_task = await save_synthesis_task(db, request)

    # 将已有的 DatasetFiles 记录保存到 t_data_synthesis_file_instances
    for f in dataset_files:
        file_instance = DataSynthesisFileInstance(
            id=str(uuid.uuid4()),  # 使用新的 UUID 作为文件任务记录的主键，避免与 DatasetFiles 主键冲突
            synthesis_instance_id=synthesis_task.id,
            file_name=f.file_name,
            source_file_id=str(f.id),
            target_file_location=synthesis_task.result_data_location or "",
            status="pending",
            total_chunks=0,
            processed_chunks=0,
            created_by="system",
            updated_by="system",
        )
        db.add(file_instance)

    if dataset_files:
        await db.commit()

    generation_service = GenerationService(db)
    # 异步处理任务：只传任务 ID，后台任务中使用新的 DB 会话重新加载任务对象
    background_tasks.add_task(generation_service.process_task, synthesis_task.id)

    return StandardResponse(
        code=200,
        message="success",
        data=synthesis_task,
    )


@router.get("/task/{task_id}", response_model=StandardResponse[DataSynthesisTaskItem])
async def get_synthesis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取数据合成任务详情"""
    result = await db.get(DataSynthesisInstance, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Synthesis task not found")

    return StandardResponse(
        code=200,
        message="success",
        data=result,
    )


@router.get("/tasks", response_model=StandardResponse[PagedDataSynthesisTaskResponse], status_code=200)
async def list_synthesis_tasks(
    page: int = 1,
    page_size: int = 10,
    synthesis_type: str | None = None,
    status: str | None = None,
    name: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    """分页列出所有数据合成任务"""
    query = select(DataSynthesisInstance)
    if synthesis_type:
        query = query.filter(DataSynthesisInstance.synthesis_type == synthesis_type)
    if status:
        query = query.filter(DataSynthesisInstance.status == status)
    if name:
        query = query.filter(DataSynthesisInstance.name.like(f"%{name}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    rows = result.scalars().all()

    task_items = [
        DataSynthesisTaskItem(
            id=row.id,
            name=row.name,
            description=row.description,
            status=row.status,
            synthesis_type=row.synthesis_type,
            model_id=row.model_id,
            progress=row.progress,
            result_data_location=row.result_data_location,
            text_split_config=row.text_split_config,
            synthesis_config=row.synthesis_config,
            source_file_id=row.source_file_id,
            total_files=row.total_files,
            processed_files=row.processed_files,
            total_chunks=row.total_chunks,
            processed_chunks=row.processed_chunks,
            total_synthesis_data=row.total_synthesis_data,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
        )
        for row in rows
    ]

    paged = PagedDataSynthesisTaskResponse(
        content=task_items,
        totalElements=total,
        totalPages=(total + page_size - 1) // page_size,
        page=page,
        size=page_size,
    )

    return StandardResponse(
        code=200,
        message="Success",
        data=paged,
    )


@router.delete("/task/{task_id}", response_model=StandardResponse[None])
async def delete_synthesis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除数据合成任务"""
    task = await db.get(DataSynthesisInstance, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Synthesis task not found")

    # 1. 删除与该任务相关的 SynthesisData、Chunk、File 记录
    # 先查出所有文件任务 ID
    file_result = await db.execute(
        select(DataSynthesisFileInstance.id).where(
            DataSynthesisFileInstance.synthesis_instance_id == task_id
        )
    )
    file_ids = [row[0] for row in file_result.all()]

    if file_ids:
        # 删除 SynthesisData（根据文件任务ID）
        await db.execute(delete(SynthesisData).where(
                SynthesisData.synthesis_file_instance_id.in_(file_ids)
            )
        )

        # 删除 Chunk 记录
        await db.execute(delete(DataSynthesisChunkInstance).where(
                DataSynthesisChunkInstance.synthesis_file_instance_id.in_(file_ids)
            )
        )

        # 删除文件任务记录
        await db.execute(delete(DataSynthesisFileInstance).where(
                DataSynthesisFileInstance.id.in_(file_ids)
            )
        )

    # 2. 删除任务本身
    await db.delete(task)
    await db.commit()

    return StandardResponse(
        code=200,
        message="success",
        data=None,
    )


@router.delete("/task/{task_id}/{file_id}", response_model=StandardResponse[None])
async def delete_synthesis_file_task(
    task_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除数据合成任务中的文件任务，同时刷新任务表中的文件/切片数量"""
    # 先获取任务和文件任务记录
    task = await db.get(DataSynthesisInstance, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Synthesis task not found")

    file_task = await db.get(DataSynthesisFileInstance, file_id)
    if not file_task:
        raise HTTPException(status_code=404, detail="Synthesis file task not found")

    # 删除 SynthesisData（根据文件任务ID）
    await db.execute(
        delete(SynthesisData).where(
            SynthesisData.synthesis_file_instance_id == file_id
        )
    )

    # 删除 Chunk 记录
    await db.execute(delete(DataSynthesisChunkInstance).where(
            DataSynthesisChunkInstance.synthesis_file_instance_id == file_id
        )
    )

    # 删除文件任务记录
    await db.execute(
        delete(DataSynthesisFileInstance).where(
            DataSynthesisFileInstance.id == file_id
        )
    )

    # 刷新任务级别统计字段：总文件数、总文本块数、已处理文本块数
    if task.total_files and task.total_files > 0:
        task.total_files -= 1
        if task.total_files < 0:
            task.total_files = 0

    await db.commit()
    await db.refresh(task)

    return StandardResponse(
        code=200,
        message="success",
        data=None,
    )


@router.get("/prompt", response_model=StandardResponse[str])
async def get_prompt_by_type(
    synth_type: SynthesisType,
):
    prompt = get_prompt(synth_type)
    return StandardResponse(
        code=200,
        message="Success",
        data=prompt,
    )


@router.get("/task/{task_id}/files", response_model=StandardResponse[PagedDataSynthesisFileTaskResponse])
async def list_synthesis_file_tasks(
    task_id: str,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """分页获取某个数据合成任务下的文件任务列表"""
    # 先校验任务是否存在
    task = await db.get(DataSynthesisInstance, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Synthesis task not found")

    base_query = select(DataSynthesisFileInstance).where(
        DataSynthesisFileInstance.synthesis_instance_id == task_id
    )

    count_q = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    result = await db.execute(
        base_query.offset((page - 1) * page_size).limit(page_size)
    )
    rows = result.scalars().all()

    file_items = [
        DataSynthesisFileTaskItem(
            id=row.id,
            synthesis_instance_id=row.synthesis_instance_id,
            file_name=row.file_name,
            source_file_id=row.source_file_id,
            target_file_location=row.target_file_location,
            status=row.status,
            total_chunks=row.total_chunks,
            processed_chunks=row.processed_chunks,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by=row.created_by,
            updated_by=row.updated_by,
        )
        for row in rows
    ]

    paged = PagedDataSynthesisFileTaskResponse(
        content=file_items,
        totalElements=total,
        totalPages=(total + page_size - 1) // page_size,
        page=page,
        size=page_size,
    )

    return StandardResponse(
        code=200,
        message="Success",
        data=paged,
    )


@router.get("/file/{file_id}/chunks", response_model=StandardResponse[PagedDataSynthesisChunkResponse])
async def list_chunks_by_file(
    file_id: str,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """根据文件任务 ID 分页查询 chunk 记录"""
    # 校验文件任务是否存在
    file_task = await db.get(DataSynthesisFileInstance, file_id)
    if not file_task:
        raise HTTPException(status_code=404, detail="Synthesis file task not found")

    base_query = select(DataSynthesisChunkInstance).where(
        DataSynthesisChunkInstance.synthesis_file_instance_id == file_id
    )

    count_q = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    result = await db.execute(
        base_query.order_by(DataSynthesisChunkInstance.chunk_index.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.scalars().all()

    chunk_items = [
        DataSynthesisChunkItem(
            id=row.id,
            synthesis_file_instance_id=row.synthesis_file_instance_id,
            chunk_index=row.chunk_index,
            chunk_content=row.chunk_content,
            chunk_metadata=getattr(row, "chunk_metadata", None),
        )
        for row in rows
    ]

    paged = PagedDataSynthesisChunkResponse(
        content=chunk_items,
        totalElements=total,
        totalPages=(total + page_size - 1) // page_size,
        page=page,
        size=page_size,
    )

    return StandardResponse(
        code=200,
        message="Success",
        data=paged,
    )


@router.get("/chunk/{chunk_id}/data", response_model=StandardResponse[list[SynthesisDataItem]])
async def list_synthesis_data_by_chunk(
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
):
    """根据 chunk ID 查询所有合成结果数据"""
    # 可选：校验 chunk 是否存在
    chunk = await db.get(DataSynthesisChunkInstance, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    result = await db.execute(
        select(SynthesisData).where(SynthesisData.chunk_instance_id == chunk_id)
    )
    rows = result.scalars().all()

    items = [
        SynthesisDataItem(
            id=row.id,
            data=row.data,
            synthesis_file_instance_id=row.synthesis_file_instance_id,
            chunk_instance_id=row.chunk_instance_id,
        )
        for row in rows
    ]

    return StandardResponse(
        code=200,
        message="Success",
        data=items,
    )
