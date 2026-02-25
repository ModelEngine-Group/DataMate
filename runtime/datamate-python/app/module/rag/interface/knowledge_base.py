"""
知识库 API 接口

实现知识库相关的 REST API 接口
对应 Java: com.datamate.rag.indexer.interfaces.KnowledgeBaseController

接口路径调整：
- Java: /knowledge-base/*
- Python: /rag/knowledge-base/*
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import SuccessResponse
from app.db.session import get_db
from app.module.rag.schema.request import (
    KnowledgeBaseCreateReq,
    KnowledgeBaseUpdateReq,
    KnowledgeBaseQueryReq,
    AddFilesReq,
    DeleteFilesReq,
    RagFileReq,
    RetrieveReq,
    PagingQuery,
)
from app.module.rag.service.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-base", tags=["知识库管理"])


@router.post("/create", response_model=SuccessResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreateReq,
    db: AsyncSession = Depends(get_db)
):
    """创建知识库

    对应 Java: POST /knowledge-base/create

    Args:
        request: 知识库创建请求
        db: 数据库 session

    Returns:
        知识库 ID
    """
    service = KnowledgeBaseService(db)
    knowledge_base_id = await service.create(request)
    return SuccessResponse(data=knowledge_base_id)


@router.put("/{knowledge_base_id}", response_model=SuccessResponse)
async def update_knowledge_base(
    knowledge_base_id: str,
    request: KnowledgeBaseUpdateReq,
    db: AsyncSession = Depends(get_db)
):
    """更新知识库

    对应 Java: PUT /knowledge-base/{id}

    Args:
        knowledge_base_id: 知识库 ID
        request: 知识库更新请求
        db: 数据库 session
    """
    service = KnowledgeBaseService(db)
    await service.update(knowledge_base_id, request)
    return SuccessResponse(message="知识库更新成功")


@router.delete("/{knowledge_base_id}", response_model=SuccessResponse)
async def delete_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除知识库

    对应 Java: DELETE /knowledge-base/{id}

    Args:
        knowledge_base_id: 知识库 ID
        db: 数据库 session
    """
    service = KnowledgeBaseService(db)
    await service.delete(knowledge_base_id)
    return SuccessResponse(message="知识库删除成功")


@router.get("/{knowledge_base_id}", response_model=SuccessResponse)
async def get_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取知识库详情

    对应 Java: GET /knowledge-base/{id}

    Args:
        knowledge_base_id: 知识库 ID
        db: 数据库 session

    Returns:
        知识库详情
    """
    service = KnowledgeBaseService(db)
    knowledge_base = await service.get_by_id(knowledge_base_id)
    return SuccessResponse(data=knowledge_base)


@router.post("/list", response_model=SuccessResponse)
async def list_knowledge_bases(
    request: KnowledgeBaseQueryReq,
    db: AsyncSession = Depends(get_db)
):
    """分页查询知识库列表

    对应 Java: POST /knowledge-base/list

    Args:
        request: 查询请求
        db: 数据库 session

    Returns:
        知识库列表（分页）
    """
    service = KnowledgeBaseService(db)
    result = await service.list(request)
    return SuccessResponse(data=result)


@router.post("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def add_files_to_knowledge_base(
    knowledge_base_id: str,
    request: AddFilesReq,
    db: AsyncSession = Depends(get_db)
):
    """添加文件到知识库

    对应 Java: POST /knowledge-base/{id}/files

    Args:
        knowledge_base_id: 知识库 ID
        request: 添加文件请求
        db: 数据库 session

    Returns:
        包含成功添加数量和跳过文件数量的响应
    """
    # 确保 knowledge_base_id 与 request 中的一致
    request.knowledge_base_id = knowledge_base_id

    service = KnowledgeBaseService(db)
    result = await service.add_files(request)

    message = f"文件添加成功，正在后台处理"
    if result["skipped_count"] > 0:
        message = f"成功添加 {result['success_count']} 个文件，跳过 {result['skipped_count']} 个不存在的文件"

    return SuccessResponse(
        message=message,
        data={
            "successCount": result["success_count"],
            "skippedCount": result["skipped_count"],
            "skippedFileIds": result["skipped_file_ids"]
        }
    )


@router.get("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def list_knowledge_base_files(
    knowledge_base_id: str,
    request: RagFileReq = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取知识库文件列表

    对应 Java: GET /knowledge-base/{id}/files

    Args:
        knowledge_base_id: 知识库 ID
        request: 查询请求
        db: 数据库 session

    Returns:
        文件列表（分页）
    """
    service = KnowledgeBaseService(db)
    result = await service.list_files(knowledge_base_id, request)
    return SuccessResponse(data=result)


@router.delete("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def delete_knowledge_base_files(
    knowledge_base_id: str,
    request: DeleteFilesReq,
    db: AsyncSession = Depends(get_db)
):
    """删除知识库文件

    对应 Java: DELETE /knowledge-base/{id}/files

    Args:
        knowledge_base_id: 知识库 ID
        request: 删除文件请求
        db: 数据库 session
    """
    service = KnowledgeBaseService(db)
    await service.delete_files(knowledge_base_id, request)
    return SuccessResponse(message="文件删除成功")


@router.get("/{knowledge_base_id}/files/{rag_file_id}", response_model=SuccessResponse)
async def get_file_chunks(
    knowledge_base_id: str,
    rag_file_id: str,
    paging_query: PagingQuery = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """获取指定 RAG 文件的分块列表

    对应 Java: GET /knowledge-base/{id}/files/{ragFileId}

    Args:
        knowledge_base_id: 知识库 ID
        rag_file_id: RAG 文件 ID
        paging_query: 分页参数
        db: 数据库 session

    Returns:
        文件分块列表（分页）
    """
    service = KnowledgeBaseService(db)
    result = await service.get_chunks(knowledge_base_id, rag_file_id, paging_query)
    return SuccessResponse(data=result)


@router.post("/retrieve", response_model=SuccessResponse)
async def retrieve_knowledge_base(
    request: RetrieveReq,
    db: AsyncSession = Depends(get_db)
):
    """检索知识库内容（向量 + BM25 混合检索）

    对应 Java: POST /knowledge-base/retrieve

    Args:
        request: 检索请求
        db: 数据库 session

    Returns:
        检索结果列表
    """
    service = KnowledgeBaseService(db)
    results = await service.retrieve(request)
    return SuccessResponse(data=results)
