from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import SuccessResponse
from app.db.session import get_db
from app.module.rag.service.rag_service import RAGService
from app.module.rag.service.knowledge_base_service import KnowledgeBaseService
from ..schema.request import QueryRequest

router = APIRouter(prefix="/rag", tags=["知识图谱 RAG"])

@router.post("/{knowledge_base_id}/process")
async def process_knowledge_base(
    knowledge_base_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    手动触发知识库文件处理（已废弃，文件处理在添加时自动触发）
    
    此接口保留用于向后兼容或手动重新处理文件
    """
    service = KnowledgeBaseService(db)
    kb = await service.kb_repo.get_by_id(knowledge_base_id)
    
    if not kb:
        return SuccessResponse(
            data=None,
            message="知识库不存在"
        )
    
    files = await service.file_repo.get_unprocessed_files(knowledge_base_id)
    if not files:
        return SuccessResponse(
            data=None,
            message="没有待处理的文件"
        )
    
    service.file_processor.start_background_processing(
        background_tasks=background_tasks,
        knowledge_base_id=str(kb.id),
        knowledge_base_name=str(kb.name),
        knowledge_base_type=str(kb.type or "DOCUMENT"),
        request_data={"knowledge_base_id": knowledge_base_id, "files": []},
    )
    
    return SuccessResponse(
        data=None,
        message=f"已开始处理 {len(files)} 个文件"
    )

@router.post("/query")
async def query_knowledge_graph(payload: QueryRequest, rag_service: RAGService = Depends()):
    """
    使用给定的查询文本和知识库 ID 查询知识图谱（LightRAG）或向量检索
    """
    result = await rag_service.query_rag(payload.query, payload.knowledge_base_id)
    return SuccessResponse(data=result)
