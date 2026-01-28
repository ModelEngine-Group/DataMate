from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.module.rag.service.rag_service import RAGService
from app.module.shared.schema import StandardResponse
from ..schema.rag_schema import QueryRequest

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/process/{knowledge_base_id}")
async def process_knowledge_base(knowledge_base_id: str, rag_service: RAGService = Depends()):
    """
    Process all unprocessed files in a knowledge base.
    """
    try:
        await rag_service.init_graph_rag(knowledge_base_id)
        return StandardResponse(
            code=200,
            message="Processing started for knowledge base.",
            data=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_knowledge_graph(payload: QueryRequest, rag_service: RAGService = Depends()):
    """
    Query the knowledge graph with the given query text and knowledge base ID.
    """
    try:
        result = await rag_service.query_rag(payload.query, payload.knowledge_base_id)
        return StandardResponse(code=200, message="success", data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
