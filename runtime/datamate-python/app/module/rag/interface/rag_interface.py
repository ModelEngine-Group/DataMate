from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.module.rag.service.rag_service import RAGService
from app.module.shared.schema import StandardResponse
from ..schema.rag_schema import QueryRequest

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/process/{knowledge_base_id}")
async def process_knowledge_base(knowledge_base_id: str, db: AsyncSession = Depends(get_db)):
    """
    Process all unprocessed files in a knowledge base.
    """
    try:
        await RAGService(db).init_graph_rag(knowledge_base_id)
        return StandardResponse(
            code=200,
            message="Processing started for knowledge base.",
            data=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_knowledge_graph(payload: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Query the knowledge graph with the given query text and knowledge base ID.
    """
    try:
        rag_service = RAGService(db)
        result = await rag_service.query_rag(payload.query, payload.knowledge_base_id)
        return StandardResponse(code=200, message="success", data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
