import asyncio
from typing import Optional
from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.db.models import Dataset
from app.db.session import get_db
from app.module.shared.schema import StandardResponse
from app.module.synthesis.schema.qa_generation import (
    CreateQATaskRequest,
    CreateQATaskResponse,
    PagedQATaskResponse,
    QATaskItem,
    QATaskDetailResponse,
    TargetDatasetInfo,
)
from app.module.synthesis.service.qa_generation import QAGenerationService
from app.db.models.qa_generation import QAGenerationInstance

router = APIRouter(
    prefix="/qa-generation",
    tags=["synthesis/qa-generation"],
)
logger = get_logger(__name__)


async def validate_source_dataset(db: AsyncSession, dataset_id: str) -> Dataset:
    """验证源数据集是否存在"""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Source dataset {dataset_id} not found")
    return dataset


async def create_target_dataset(
    db: AsyncSession,
    source_dataset: Dataset,
    task_name: str,
) -> Dataset:
    """创建目标数据集用于存储生成的 JSONL 文件"""
    target_dataset = Dataset(
        name=f"{task_name}_QA_JSONL",
        description=f"QA生成任务 {task_name} 的输出结果 (JSONL格式)",
        dataset_type="QA",  # 明确标记为QA类型
        category="生成的QA数据集",
        format="JSONL",
        status="ACTIVE",
    )
    db.add(target_dataset)
    await db.commit()
    await db.refresh(target_dataset)
    return target_dataset


@router.post("", response_model=StandardResponse[CreateQATaskResponse], status_code=200)
async def create_qa_task(
    req: CreateQATaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    创建QA生成任务
    
    Path: /api/generation/qa-generation
    
    新版本功能:
    1. 支持通过 file_ids 列表指定要处理的文件（来自 t_dm_dataset_files）
    2. 自动检测并支持 .txt, .md, .json 格式文件
    3. 支持用户自定义 extra_prompt，插入到 LLM Prompt 中
    4. 输出 Alpaca 格式的 JSONL 文件
    
    完整数据流:
    1. 根据 file_ids 从 t_dm_dataset_files 读取指定文件
    2. 对每个文件进行文本切片和QA生成
    3. 将QA对存入 t_qa_pairs 表 (text_chunk, question, answer)
    4. 导出为 Alpaca 格式 JSONL (instruction, input, output)
    5. 将 JSONL 文件信息存入 t_dm_dataset_files 和 t_dm_datasets
    
    """
    try:
        logger.info(f"Creating QA generation task: {req.name}, files: {len(req.source_file_ids)}")

        # 1. 验证源文件是否存在
        service = QAGenerationService(db)
        source_files = await service.get_source_files_by_ids(req.source_file_ids)
        if not source_files:
            raise HTTPException(
                status_code=404, 
                detail=f"No valid files found from provided file IDs (supported: .txt, .md, .json)"
            )
        
        logger.info(f"Found {len(source_files)} valid source files")

        # 2. 创建目标数据集
        # 使用第一个文件所属的数据集信息作为参考
        first_file_dataset_result = await db.execute(
            select(Dataset).where(Dataset.id == source_files[0].dataset_id)
        )
        ref_dataset = first_file_dataset_result.scalar_one_or_none()
        
        target_dataset = Dataset(
            name=f"{req.name}_QA_Alpaca",
            description=f"QA生成任务 {req.name} 的输出结果 (Alpaca JSONL格式)",
            dataset_type="QA",
            category="生成的QA数据集",
            format="JSONL",
            status="ACTIVE",
        )
        db.add(target_dataset)
        await db.commit()
        await db.refresh(target_dataset)
        logger.info(f"Target dataset created: {target_dataset.id}")

        # 3. 创建QA生成任务
        task = await service.create_task(
            name=req.name,
            description=req.description,
            source_file_ids=req.source_file_ids,
            target_dataset_id=target_dataset.id,
            text_split_config=req.text_split_config.model_dump(),
            qa_generation_config=req.qa_generation_config.model_dump(),
            llm_api_key=req.llm_api_key,
            llm_base_url=req.llm_base_url,
            extra_prompt=req.extra_prompt,
        )

        # 4. 在后台执行任务
        background_tasks.add_task(service.process_task, task.id)
        logger.info(f"QA generation task {task.id} added to background tasks")

        # 5. 构造响应
        response = CreateQATaskResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            status=task.status,
            source_file_ids=req.source_file_ids,
            target_dataset_id=task.target_dataset_id,
            text_split_config=req.text_split_config,
            qa_generation_config=req.qa_generation_config,
            targetDataset=TargetDatasetInfo(
                id=target_dataset.id,
                name=target_dataset.name,
                datasetType=target_dataset.dataset_type,
                status=target_dataset.status,
            ),
            created_at=task.created_at.isoformat() if task.created_at else None,
        )

        return StandardResponse(
            code=200,
            message="QA generation task created successfully",
            data=response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create QA generation task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=StandardResponse[PagedQATaskResponse], status_code=200)
async def list_qa_tasks(
    page: int = Query(0, ge=0, description="页码，从0开始"),
    size: int = Query(10, ge=1, le=100, description="每页大小"),
    name: Optional[str] = Query(None, description="任务名称(模糊搜索)"),
    status: Optional[str] = Query(None, description="任务状态"),
    db: AsyncSession = Depends(get_db),
):
    """
    分页查询QA生成任务列表
    
    Path: /api/generation/qa-generation?page=0&size=10
    """
    try:
        service = QAGenerationService(db)
        tasks, total = await service.list_tasks(
            page=page,
            size=size,
            name=name,
            status=status,
        )

        # 获取关联的数据集信息
        source_dataset_ids = {t.source_dataset_id for t in tasks if t.source_dataset_id}
        target_dataset_ids = {t.target_dataset_id for t in tasks if t.target_dataset_id}
        all_dataset_ids = source_dataset_ids | target_dataset_ids

        dataset_map = {}
        if all_dataset_ids:
            result = await db.execute(
                select(Dataset).where(Dataset.id.in_(all_dataset_ids))
            )
            datasets = result.scalars().all()
            dataset_map = {ds.id: ds for ds in datasets}

        # 构造响应
        content = []
        for task in tasks:
            source_dataset = dataset_map.get(task.source_dataset_id)
            target_dataset = dataset_map.get(task.target_dataset_id)

            content.append(
                QATaskItem(
                    id=task.id,
                    name=task.name,
                    description=task.description,
                    status=task.status,
                    source_dataset_id=task.source_dataset_id,
                    source_dataset_name=source_dataset.name if source_dataset else None,
                    target_dataset_id=task.target_dataset_id,
                    target_dataset_name=target_dataset.name if target_dataset else None,
                    total_files=task.total_files,
                    processed_files=task.processed_files,
                    total_chunks=task.total_chunks,
                    processed_chunks=task.processed_chunks,
                    total_qa_pairs=task.total_qa_pairs,
                    created_at=task.created_at.isoformat() if task.created_at else None,
                    updated_at=task.updated_at.isoformat() if task.updated_at else None,
                )
            )

        total_pages = ceil(total / size) if size > 0 else 0

        return StandardResponse(
            code=200,
            message="QA tasks retrieved successfully",
            data=PagedQATaskResponse(
                content=content,
                totalElements=total,
                totalPages=total_pages,
                page=page,
                size=size,
            ),
        )

    except Exception as e:
        logger.error(f"Failed to list QA tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=StandardResponse[QATaskDetailResponse], status_code=200)
async def get_qa_task_detail(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    获取QA生成任务详情
    
    Path: /api/generation/qa-generation/{task_id}
    """
    try:
        service = QAGenerationService(db)
        task = await service.get_task_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # 获取关联的数据集信息
        dataset_ids = [task.source_dataset_id]
        if task.target_dataset_id:
            dataset_ids.append(task.target_dataset_id)

        result = await db.execute(
            select(Dataset).where(Dataset.id.in_(dataset_ids))
        )
        datasets = result.scalars().all()
        dataset_map = {ds.id: ds for ds in datasets}

        source_dataset = dataset_map.get(task.source_dataset_id)
        target_dataset = dataset_map.get(task.target_dataset_id) if task.target_dataset_id else None

        # 构造响应
        response = QATaskDetailResponse(
            id=task.id,
            name=task.name,
            description=task.description,
            status=task.status,
            source_dataset_id=task.source_dataset_id,
            target_dataset_id=task.target_dataset_id,
            text_split_config=task.text_split_config,
            qa_generation_config=task.qa_generation_config,
            source_dataset={
                "id": source_dataset.id,
                "name": source_dataset.name,
                "type": source_dataset.dataset_type,
            } if source_dataset else {},
            target_dataset={
                "id": target_dataset.id,
                "name": target_dataset.name,
                "type": target_dataset.dataset_type,
            } if target_dataset else None,
            total_files=task.total_files,
            processed_files=task.processed_files,
            total_chunks=task.total_chunks,
            processed_chunks=task.processed_chunks,
            total_qa_pairs=task.total_qa_pairs,
            error_message=task.error_message,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

        return StandardResponse(
            code=200,
            message="QA task detail retrieved successfully",
            data=response,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get QA task detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}", response_model=StandardResponse[None], status_code=200)
async def delete_qa_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    删除QA生成任务
    
    Path: /api/generation/qa-generation/{task_id}
    """
    try:
        service = QAGenerationService(db)
        
        # 检查任务是否存在
        task = await service.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # 删除任务
        success = await service.delete_task(task_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete task")

        return StandardResponse(
            code=200,
            message="QA task deleted successfully",
            data=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete QA task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry", response_model=StandardResponse[None], status_code=200)
async def retry_qa_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    重试失败的QA生成任务
    
    Path: /api/generation/qa-generation/{task_id}/retry
    """
    try:
        service = QAGenerationService(db)
        
        # 检查任务是否存在
        task = await service.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        # 只有失败的任务才能重试
        if task.status not in ["FAILED", "COMPLETED"]:
            raise HTTPException(
                status_code=400,
                detail=f"Task status is {task.status}, only FAILED or COMPLETED tasks can be retried"
            )

        # 重置任务状态
        await service.update_task_status(task_id, "PENDING")
        await service.update_task_progress(task_id, processed_chunks=0, total_qa_pairs=0)

        # 在后台重新执行任务
        background_tasks.add_task(service.process_task, task_id)
        logger.info(f"QA generation task {task_id} retry added to background tasks")

        return StandardResponse(
            code=200,
            message="QA task retry started",
            data=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry QA task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
