"""
Operator API Routes
算子 API 路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, Form, File, Body
from fastapi.responses import FileResponse

from app.core.logging import get_logger
from app.db.models.operator import Operator, CategoryRelation, OperatorRelease
from app.db.session import get_db
from app.module.operator.parsers import ParserHolder
from app.module.operator.repository import (
    OperatorRepository,
    CategoryRelationRepository,
    OperatorReleaseRepository,
)
from app.module.operator.schema import (
    OperatorDto,
    OperatorUpdateDto,
    OperatorListRequest,
)
from app.module.operator.service import OperatorService
from app.module.shared.chunk_upload_repository import ChunkUploadRepository
from app.module.shared.file_service import FileService
from app.module.shared.schema import StandardResponse, PaginatedData

logger = get_logger(__name__)

router = APIRouter(prefix="/operators", tags=["Operator"])


def get_operator_service() -> OperatorService:
    """获取算子服务实例"""
    return OperatorService(
        operator_repo=OperatorRepository(Operator()),
        category_relation_repo=CategoryRelationRepository(CategoryRelation()),
        operator_release_repo=OperatorReleaseRepository(OperatorRelease()),
        parser_holder=ParserHolder(),
        file_service=FileService(ChunkUploadRepository()),
    )


@router.post(
    "/list",
    response_model=StandardResponse[PaginatedData[OperatorDto]],
    summary="查询算子列表",
    description="根据参数查询算子列表（支持分页、分类过滤、关键词搜索）",
    tags=['mcp']
)
async def list_operators(
    request: OperatorListRequest,
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db),
):
    """查询算子列表"""
    operators = await service.get_operators(
        page=request.page,
        size=request.size,
        categories=request.categories,
        keyword=request.keyword,
        is_star=request.is_star,
        db=db
    )

    count = await service.count_operators(
        categories=request.categories,
        keyword=request.keyword,
        is_star=request.is_star,
        db=db
    )

    total_pages = (count + request.size - 1) // request.size

    return StandardResponse(
        code="0",
        message="success",
        data=PaginatedData(
            page=request.page,
            size=request.size,
            total_elements=count,
            total_pages=total_pages,
            content=operators,
        )
    )


@router.get(
    "/{operator_id}",
    response_model=StandardResponse[OperatorDto],
    summary="获取算子详情",
    description="根据 ID 获取算子详细信息"
)
async def get_operator(
    operator_id: str,
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db)
):
    """获取算子详情"""
    operator = await service.get_operator_by_id(operator_id, db)
    operator.file_name = None
    return StandardResponse(code="0", message="success", data=operator)


@router.put(
    "/{operator_id}",
    response_model=StandardResponse[OperatorDto],
    summary="更新算子",
    description="更新算子信息"
)
async def update_operator(
    operator_id: str,
    request: OperatorUpdateDto,
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db)
):
    """更新算子"""
    operator = await service.update_operator(operator_id, request, db)
    await db.commit()
    return StandardResponse(code="0", message="success", data=operator)


@router.post(
    "/create",
    response_model=StandardResponse[OperatorDto],
    summary="创建算子",
    description="创建新算子"
)
async def create_operator(
    request: OperatorDto,
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db)
):
    """创建算子"""
    operator = await service.create_operator(request, db)
    await db.commit()
    return StandardResponse(code="0", message="success", data=operator)


@router.post(
    "/upload",
    response_model=StandardResponse[OperatorDto],
    summary="上传算子",
    description="上传算子文件并解析元数据"
)
async def upload_operator(
    request: dict = Body(...),
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db),
):
    """上传算子"""
    file_name = request.get("fileName")
    if not file_name:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="fileName is required")
    operator = await service.upload_operator(file_name, db)
    return StandardResponse(code="0", message="success", data=operator)


@router.post(
    "/upload/pre-upload",
    response_model=StandardResponse[str],
    summary="预上传",
    description="获取预上传 ID，用于分块上传"
)
async def pre_upload(
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db),
):
    """预上传"""
    req_id = await service.pre_upload(db)
    await db.commit()
    return StandardResponse(
        code="0",
        message="success",
        data=req_id,
    )


@router.post(
    "/upload/chunk",
    response_model=StandardResponse[dict],
    summary="分块上传",
    description="分块上传算子文件"
)
async def chunk_upload(
    req_id: str = Form(..., alias="reqId", description="预上传ID"),
    file_no: int = Form(1, alias="fileNo", description="文件编号"),
    file_name: str = Form(..., alias="fileName", description="文件名"),
    total_chunk_num: int = Form(1, alias="totalChunkNum", description="总分块数"),
    chunk_no: int = Form(1, alias="chunkNo", description="当前分块号"),
    file: UploadFile = File(...),
    check_sum_hex: Optional[str] = Form(None, alias="checkSumHex", description="校验和"),
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db),
):
    """分块上传"""
    file_content = await file.read()
    result = await service.chunk_upload(
        req_id=req_id,
        file_no=file_no,
        file_name=file_name,
        total_chunk_num=total_chunk_num,
        chunk_no=chunk_no,
        check_sum_hex=check_sum_hex,
        file_content=file_content,
        db=db
    )
    await db.commit()
    return StandardResponse(code="0", message="success", data=result.dict())


@router.delete(
    "/{operator_id}",
    response_model=StandardResponse[None],
    summary="删除算子",
    description="删除算子"
)
async def delete_operator(
    operator_id: str,
    service: OperatorService = Depends(get_operator_service),
    db = Depends(get_db),
):
    """删除算子"""
    await service.delete_operator(operator_id, db)
    await db.commit()
    return StandardResponse(code="0", message="success", data=None)


@router.get(
    "/examples/download",
    response_class=FileResponse,
    summary="下载示例算子",
    description="下载示例算子文件"
)
async def download_example_operator(
    service: OperatorService = Depends(get_operator_service),
):
    """下载示例算子"""
    from app.module.operator.constants import EXAMPLE_OPERATOR_PATH

    example_path = EXAMPLE_OPERATOR_PATH
    file_path = service.download_example_operator(example_path)
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )
