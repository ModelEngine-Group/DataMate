from fastapi import APIRouter, Depends

from app.core.exception import ErrorCodes, BusinessError, SuccessResponse
from app.db.session import get_db
from app.module.rag.service.rag_service import RAGService
from app.module.shared.schema import StandardResponse
from ..schema.rag_schema import QueryRequest

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/process/{knowledge_base_id}")
async def process_knowledge_base(knowledge_base_id: str, rag_service: RAGService = Depends()):
    """
    处理知识库中所有未处理的文件
    """
    await rag_service.init_graph_rag(knowledge_base_id)
    return SuccessResponse(
        data=None,
        message="Processing started for knowledge base."
    )

@router.post("/query")
async def query_knowledge_graph(payload: QueryRequest, rag_service: RAGService = Depends()):
    """
    使用给定的查询文本和知识库 ID 查询知识图谱
    """
    result = await rag_service.query_rag(payload.query, payload.knowledge_base_id)
    return SuccessResponse(data=result)
