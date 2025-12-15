import uuid
from typing import cast

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.data_synthesis import (
    save_synthesis_task,
    DataSynthInstance,
    DataSynthesisFileInstance,
    DataSynthesisChunkInstance,
    SynthesisData,
)
from app.db.models.dataset_management import DatasetFiles
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
    SynthesisDataUpdateRequest,
    BatchDeleteSynthesisDataRequest,
)
from app.module.generation.service.export_service import SynthesisDatasetExporter, SynthesisExportError
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
    synth_files = []
    for f in dataset_files:
        file_instance = DataSynthesisFileInstance(
            id=str(uuid.uuid4()),  # 使用新的 UUID 作为文件任务记录的主键，避免与 DatasetFiles 主键冲突
            synthesis_instance_id=synthesis_task.id,
            file_name=f.file_name,
            source_file_id=str(f.id),
            status="pending",
            total_chunks=0,
            processed_chunks=0,
            created_by="system",
            updated_by="system",
        )
        synth_files.append(file_instance)

    if dataset_files:
        db.add_all(synth_files)
        await db.commit()

    generation_service = GenerationService(db)
    # 异步处理任务：只传任务 ID，后台任务中使用新的 DB 会话重新加载任务对象
    background_tasks.add_task(generation_service.process_task, synthesis_task.id)

    # 将 ORM 对象包装成 DataSynthesisTaskItem，兼容新字段从 synth_config 还原

    task_item = DataSynthesisTaskItem(
        id=synthesis_task.id,
        name=synthesis_task.name,
        description=synthesis_task.description,
        status=synthesis_task.status,
        synthesis_type=synthesis_task.synth_type,
        total_files=synthesis_task.total_files,
        created_at=synthesis_task.created_at,
        updated_at=synthesis_task.updated_at,
        created_by=synthesis_task.created_by,
        updated_by=synthesis_task.updated_by,
    )

    return StandardResponse(
        code=200,
        message="success",
        data=task_item,
    )


@router.get("/task/{task_id}", response_model=StandardResponse[DataSynthesisTaskItem])
async def get_synthesis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取数据合成任务详情"""
    synthesis_task = await db.get(DataSynthInstance, task_id)
    if not synthesis_task:
        raise HTTPException(status_code=404, detail="Synthesis task not found")

    task_item = DataSynthesisTaskItem(
        id=synthesis_task.id,
        name=synthesis_task.name,
        description=synthesis_task.description,
        status=synthesis_task.status,
        synthesis_type=synthesis_task.synth_type,
        total_files=synthesis_task.total_files,
        created_at=synthesis_task.created_at,
        updated_at=synthesis_task.updated_at,
        created_by=synthesis_task.created_by,
        updated_by=synthesis_task.updated_by,
    )
    return StandardResponse(
        code=200,
        message="success",
        data=task_item,
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
    """分页列出所有数据合成任务，默认按创建时间倒序"""
    query = select(DataSynthInstance)
    if synthesis_type:
        query = query.filter(DataSynthInstance.synth_type == synthesis_type)
    if status:
        query = query.filter(DataSynthInstance.status == status)
    if name:
        query = query.filter(DataSynthInstance.name.like(f"%{name}%"))

    # 默认按创建时间倒序排列
    query = query.order_by(DataSynthInstance.created_at.desc())

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10

    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    rows = result.scalars().all()

    task_items: list[DataSynthesisTaskItem] = []
    for row in rows:
        synth_cfg = getattr(row, "synth_config", {}) or {}
        text_split_cfg = synth_cfg.get("text_split_config") or {}
        synthesis_cfg = synth_cfg.get("synthesis_config") or {}
        source_file_ids = synth_cfg.get("source_file_id") or []
        model_id = synth_cfg.get("model_id")
        result_location = synth_cfg.get("result_data_location")

        task_items.append(
            DataSynthesisTaskItem(
                id=str(row.id),
                name=str(row.name),
                description=cast(str | None, row.description),
                status=cast(str | None, row.status),
                synthesis_type=str(row.synth_type),
                model_id=model_id or "",
                progress=int(cast(int, row.progress)),
                result_data_location=result_location,
                text_split_config=text_split_cfg,
                synthesis_config=synthesis_cfg,
                source_file_id=list(source_file_ids),
                total_files=int(cast(int, row.total_files)),
                processed_files=int(cast(int, row.processed_files)),
                total_chunks=int(cast(int, row.total_chunks)),
                processed_chunks=int(cast(int, row.processed_chunks)),
                total_synthesis_data=int(cast(int, row.total_synth_data)),
                created_at=row.created_at,
                updated_at=row.updated_at,
                created_by=row.created_by,
                updated_by=row.updated_by,
            )
        )

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


@router.delete("/task/{task_id}", response_model=StandardResponse)
async def delete_synthesis_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除数据合成任务"""
    task = await db.get(DataSynthInstance, task_id)
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


@router.delete("/task/{task_id}/{file_id}", response_model=StandardResponse)
async def delete_synthesis_file_task(
    task_id: str,
    file_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除数据合成任务中的文件任务，同时刷新任务表中的文件/切片数量"""
    # 先获取任务和文件任务记录
    task = await db.get(DataSynthInstance, task_id)
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
    task = await db.get(DataSynthInstance, task_id)
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


@router.post("/task/{task_id}/export-dataset/{dataset_id}", response_model=StandardResponse[str])
async def export_synthesis_task_to_dataset(
    task_id: str,
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
):
    """将指定合成任务的全部合成数据归档到已有数据集中。

    规则：
    - 以原始文件为维度，每个原始文件生成一个 JSONL 文件；
    - JSONL 文件名称与原始文件名称完全一致；
    - 仅写入文件，不再创建数据集。
    """
    exporter = SynthesisDatasetExporter(db)
    try:
        dataset = await exporter.export_task_to_dataset(task_id, dataset_id)
    except SynthesisExportError as e:
        logger.error(
            "Failed to export synthesis task %s to dataset %s: %s",
            task_id,
            dataset_id,
            e,
        )
        raise HTTPException(status_code=400, detail=str(e))

    return StandardResponse(
        code=200,
        message="success",
        data=dataset.id,
    )


@router.delete("/chunk/{chunk_id}", response_model=StandardResponse)
async def delete_chunk_with_data(
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除单条 t_data_synthesis_chunk_instances 记录及其关联的所有 t_data_synthesis_data"""
    chunk = await db.get(DataSynthesisChunkInstance, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    # 先删除与该 chunk 关联的合成数据
    await db.execute(
        delete(SynthesisData).where(SynthesisData.chunk_instance_id == chunk_id)
    )

    # 再删除 chunk 本身
    await db.execute(
        delete(DataSynthesisChunkInstance).where(
            DataSynthesisChunkInstance.id == chunk_id
        )
    )

    await db.commit()

    return StandardResponse(code=200, message="success", data=None)


@router.delete("/chunk/{chunk_id}/data", response_model=StandardResponse)
async def delete_synthesis_data_by_chunk(
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
):
    """仅删除指定 chunk 下的全部 t_data_synthesis_data 记录，返回删除条数"""
    chunk = await db.get(DataSynthesisChunkInstance, chunk_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")

    result = await db.execute(
        delete(SynthesisData).where(SynthesisData.chunk_instance_id == chunk_id)
    )
    deleted = int(getattr(result, "rowcount", 0) or 0)

    await db.commit()

    return StandardResponse(code=200, message="success", data=deleted)


@router.delete("/data/batch", response_model=StandardResponse)
async def batch_delete_synthesis_data(
    request: BatchDeleteSynthesisDataRequest,
    db: AsyncSession = Depends(get_db),
):
    """批量删除 t_data_synthesis_data 记录"""
    if not request.ids:
        return StandardResponse(code=200, message="success", data=0)

    result = await db.execute(
        delete(SynthesisData).where(SynthesisData.id.in_(request.ids))
    )
    deleted = int(getattr(result, "rowcount", 0) or 0)
    await db.commit()

    return StandardResponse(code=200, message="success", data=deleted)


@router.patch("/data/{data_id}", response_model=StandardResponse)
async def update_synthesis_data_field(
    data_id: str,
    body: SynthesisDataUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """修改单条 t_data_synthesis_data.data 的完整 JSON

    前端传入完整 JSON，后端直接覆盖原有 data 字段，不做局部 merge。
    """
    record = await db.get(SynthesisData, data_id)
    if not record:
        raise HTTPException(status_code=404, detail="Synthesis data not found")

    # 直接整体覆盖 data 字段
    record.data = body.data

    await db.commit()
    await db.refresh(record)

    return StandardResponse(
        code=200,
        message="success",
        data=SynthesisDataItem(
            id=record.id,
            data=record.data,
            synthesis_file_instance_id=record.synthesis_file_instance_id,
            chunk_instance_id=record.chunk_instance_id,
        ),
    )
