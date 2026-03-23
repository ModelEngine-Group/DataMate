"""
知识库 API 接口

实现知识库相关的 REST API 接口。
对应 Java: com.datamate.rag.indexer.interfaces.KnowledgeBaseController
"""
import json

from fastapi import APIRouter, Depends, BackgroundTasks
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
    ChunkFilterQuery,
    QueryRequest,
    ChunkUpdateReq,
)
from app.module.rag.service.knowledge_base_service import KnowledgeBaseService
from app.module.rag.service.unified_retrieval_service import UnifiedRetrievalService

router = APIRouter(prefix="/knowledge-base", tags=["知识库管理"])


@router.post("/create", response_model=SuccessResponse)
async def create_knowledge_base(
    request: KnowledgeBaseCreateReq,
    db: AsyncSession = Depends(get_db),
):
    """创建知识库"""
    service = KnowledgeBaseService(db)
    knowledge_base_id = await service.create(request)
    return SuccessResponse(data=knowledge_base_id)


@router.put("/{knowledge_base_id}", response_model=SuccessResponse)
async def update_knowledge_base(
    knowledge_base_id: str,
    request: KnowledgeBaseUpdateReq,
    db: AsyncSession = Depends(get_db),
):
    """更新知识库"""
    service = KnowledgeBaseService(db)
    await service.update(knowledge_base_id, request)
    return SuccessResponse(message="知识库更新成功")


@router.delete("/{knowledge_base_id}", response_model=SuccessResponse)
async def delete_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除知识库"""
    service = KnowledgeBaseService(db)
    await service.delete(knowledge_base_id)
    return SuccessResponse(message="知识库删除成功")


@router.get("/{knowledge_base_id}", response_model=SuccessResponse)
async def get_knowledge_base(
    knowledge_base_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取知识库详情"""
    service = KnowledgeBaseService(db)
    knowledge_base = await service.get_by_id(knowledge_base_id)
    return SuccessResponse(data=knowledge_base)


@router.post("/list", response_model=SuccessResponse)
async def list_knowledge_bases(
    request: KnowledgeBaseQueryReq,
    db: AsyncSession = Depends(get_db),
):
    """分页查询知识库列表"""
    service = KnowledgeBaseService(db)
    result = await service.list(request)
    return SuccessResponse(data=result)


@router.post("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def add_files_to_knowledge_base(
    knowledge_base_id: str,
    request: AddFilesReq,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """添加文件到知识库

    文件记录存入数据库后立即返回，后台异步处理文件。
    """
    request.knowledge_base_id = knowledge_base_id

    service = KnowledgeBaseService(db)
    result = await service.add_files(request, background_tasks)

    message = f"文件添加成功，正在后台处理 {result['success_count']} 个文件"
    if result["skipped_count"] > 0:
        message = f"成功添加 {result['success_count']} 个文件，跳过 {result['skipped_count']} 个不存在的文件"

    return SuccessResponse(
        message=message,
        data={
            "successCount": result["success_count"],
            "skippedCount": result["skipped_count"],
            "skippedFileIds": result["skipped_file_ids"],
        },
    )


@router.get("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def list_knowledge_base_files(
    knowledge_base_id: str,
    request: RagFileReq = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """获取知识库文件列表"""
    service = KnowledgeBaseService(db)
    result = await service.list_files(knowledge_base_id, request)
    return SuccessResponse(data=result)


@router.delete("/{knowledge_base_id}/files", response_model=SuccessResponse)
async def delete_knowledge_base_files(
    knowledge_base_id: str,
    request: DeleteFilesReq,
    db: AsyncSession = Depends(get_db),
):
    """删除知识库文件"""
    service = KnowledgeBaseService(db)
    await service.delete_files(knowledge_base_id, request)
    return SuccessResponse(message="文件删除成功")


@router.get("/{knowledge_base_id}/files/{rag_file_id}", response_model=SuccessResponse)
async def get_file_chunks(
    knowledge_base_id: str,
    rag_file_id: str,
    query: ChunkFilterQuery = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """获取指定 RAG 文件的分块列表"""
    service = UnifiedRetrievalService(db)
    result = await service.get_chunks(knowledge_base_id, rag_file_id, query)
    return SuccessResponse(data=result)


@router.put("/{knowledge_base_id}/chunks/{chunk_id}", response_model=SuccessResponse)
async def update_chunk(
    knowledge_base_id: str,
    chunk_id: str,
    request: ChunkUpdateReq,
    db: AsyncSession = Depends(get_db),
):
    """更新指定分块的文本和元数据"""
    service = KnowledgeBaseService(db)
    await service.update_chunk(
        knowledge_base_id=knowledge_base_id,
        chunk_id=chunk_id,
        text=request.text,
        metadata=request.metadata,
    )
    return SuccessResponse(message="分块更新成功")


@router.delete("/{knowledge_base_id}/chunks/{chunk_id}", response_model=SuccessResponse)
async def delete_chunk(
    knowledge_base_id: str,
    chunk_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除指定分块"""
    service = KnowledgeBaseService(db)
    await service.delete_chunk(
        knowledge_base_id=knowledge_base_id,
        chunk_id=chunk_id,
    )
    return SuccessResponse(message="分块删除成功")


@router.post("/retrieve", response_model=SuccessResponse)
async def retrieve_knowledge_base(
    request: RetrieveReq,
    db: AsyncSession = Depends(get_db),
):
    """检索知识库内容（统一检索接口，兼容旧版本格式）"""
    service = UnifiedRetrievalService(db)
    results = await service.search(request)

    legacy_results = []
    for item in results:
        legacy_item = {
            "entity": {
                "metadata": json.dumps(item.get("metadata", {}), ensure_ascii=False),
                "text": item.get("text", ""),
                "id": item.get("id", ""),
            },
            "score": item.get("score", 0.0),
            "id": item.get("id", ""),
            "knowledgeBaseId": item.get("knowledgeBaseId", ""),
            "knowledgeBaseName": item.get("knowledgeBaseName", ""),
        }
        legacy_results.append(legacy_item)

    return SuccessResponse(data=legacy_results)

@router.post("/v2/retrieve", response_model=SuccessResponse)
async def v2_retrieve_knowledge_base(
    request: RetrieveReq,
    db: AsyncSession = Depends(get_db),
):
    """检索知识库内容（统一检索接口）"""
    service = UnifiedRetrievalService(db)
    results = await service.search(request)
    return SuccessResponse(data=results)


@router.post("/query", response_model=SuccessResponse)
async def query_knowledge_base(
    payload: QueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """查询知识库（支持向量检索和知识图谱）

    根据知识库类型自动选择查询策略：
    - DOCUMENT: 向量检索
    - GRAPH: 知识图谱查询
    """
    service = UnifiedRetrievalService(db)
    result = await service.query(
        knowledge_base_id=payload.knowledge_base_id,
        node_label=payload.query,
    )
    return SuccessResponse(data=result)
