from fastapi import APIRouter, Depends

from app.core.exception import SuccessResponse
from app.module.rag.service.rag_service import RAGService
from ..schema.request import QueryRequest

router = APIRouter(prefix="/rag", tags=["知识图谱 RAG"])

@router.post("/{knowledge_base_id}/process")
async def process_knowledge_base(knowledge_base_id: str, rag_service: RAGService = Depends()):
    """
    处理知识库中所有未处理的文件（LightRAG）

    接口路径调整：
    - 旧路径: /rag/process/{id}
    - 新路径: /rag/graph/{id}/process
    """
    await rag_service.init_graph_rag(knowledge_base_id)
    return SuccessResponse(
        data=None,
        message="Processing started for knowledge base."
    )

@router.post("/query")
async def query_knowledge_graph(payload: QueryRequest, rag_service: RAGService = Depends()):
    """
    使用给定的查询文本和知识库 ID 查询知识图谱（LightRAG）

    接口路径调整：
    - 旧路径: /rag/query
    - 新路径: /rag/graph/query
    """
    result = await rag_service.query_rag(payload.query, payload.knowledge_base_id)
    return SuccessResponse(data=result)
