"""FastAPI routes for Auto Annotation tasks.

These routes back the frontend AutoAnnotation module:
  - GET  /api/annotation/auto
  - POST /api/annotation/auto
  - DELETE /api/annotation/auto/{task_id}
  - GET  /api/annotation/auto/{task_id}/status (simple wrapper)

"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.module.shared.schema import StandardResponse
from app.module.dataset import DatasetManagementService
from app.core.logging import get_logger

from ..schema.auto import (
    CreateAutoAnnotationTaskRequest,
    AutoAnnotationTaskResponse,
)
from ..service.auto import AutoAnnotationTaskService


router = APIRouter(
    prefix="/auto",
    tags=["annotation/auto"],
)

logger = get_logger(__name__)
service = AutoAnnotationTaskService()


@router.get("", response_model=StandardResponse[List[AutoAnnotationTaskResponse]])
async def list_auto_annotation_tasks(
    db: AsyncSession = Depends(get_db),
):
    """获取自动标注任务列表。

    前端当前不传分页参数，这里直接返回所有未删除任务。
    """

    tasks = await service.list_tasks(db)
    return StandardResponse(
        code=200,
        message="success",
        data=tasks,
    )


@router.post("", response_model=StandardResponse[AutoAnnotationTaskResponse])
async def create_auto_annotation_task(
    request: CreateAutoAnnotationTaskRequest,
    db: AsyncSession = Depends(get_db),
):
    """创建自动标注任务。

    当前仅创建任务记录并置为 pending，实际执行由后续调度/worker 完成。
    """

    logger.info(
        "Creating auto annotation task: name=%s, dataset_id=%s, config=%s, file_ids=%s",
        request.name,
        request.dataset_id,
        request.config.model_dump(by_alias=True),
        request.file_ids,
    )

    # 尝试获取数据集名称和文件数量用于冗余字段，失败时不阻塞任务创建
    dataset_name = None
    total_images = 0
    try:
        dm_client = DatasetManagementService(db)
        # Service.get_dataset 返回 DatasetResponse，包含 name 和 fileCount
        dataset = await dm_client.get_dataset(request.dataset_id)
        if dataset is not None:
            dataset_name = dataset.name
            # 如果提供了 file_ids，则 total_images 为选中文件数；否则使用数据集文件数
            if request.file_ids:
                total_images = len(request.file_ids)
            else:
                total_images = getattr(dataset, "fileCount", 0) or 0
    except Exception as e:  # pragma: no cover - 容错
        logger.warning("Failed to fetch dataset name for auto task: %s", e)

    task = await service.create_task(
        db,
        request,
        dataset_name=dataset_name,
        total_images=total_images,
    )

    return StandardResponse(
        code=200,
        message="success",
        data=task,
    )


@router.get("/{task_id}/status", response_model=StandardResponse[AutoAnnotationTaskResponse])
async def get_auto_annotation_task_status(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取单个自动标注任务状态。

    前端当前主要通过列表轮询，这里提供按 ID 查询的补充接口。
    """

    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return StandardResponse(
        code=200,
        message="success",
        data=task,
    )


@router.delete("/{task_id}", response_model=StandardResponse[bool])
async def delete_auto_annotation_task(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """删除（软删除）自动标注任务，仅标记 deleted_at。"""

    ok = await service.soft_delete_task(db, task_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")

    return StandardResponse(
        code=200,
        message="success",
        data=True,
    )


@router.get("/{task_id}/download")
async def download_auto_annotation_result(
    task_id: str = Path(..., description="任务ID"),
    db: AsyncSession = Depends(get_db),
):
    """下载指定自动标注任务的结果 ZIP。"""

    import io
    import os
    import zipfile
    import tempfile

    # 复用服务层获取任务信息
    task = await service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not task.output_path:
        raise HTTPException(status_code=400, detail="Task has no output path")

    output_dir = task.output_path
    if not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_fd)

    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(output_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, output_dir)
                zf.write(file_path, arcname)

    file_size = os.path.getsize(tmp_path)
    if file_size == 0:
        raise HTTPException(status_code=500, detail="Generated ZIP is empty")

    def iterfile():
        with open(tmp_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk

    filename = f"{task.name}_annotations.zip"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Length": str(file_size),
    }

    return StreamingResponse(iterfile(), media_type="application/zip", headers=headers)
