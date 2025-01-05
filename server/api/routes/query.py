from fastapi import APIRouter, HTTPException, Depends, Query
from rag.rag import RAGPipeline
from api.rate_limit import rate_limit
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
rag = RAGPipeline()


@router.get("/query")
async def query(
    q: str = Query(..., description="Query string", min_length=1),
    _: None = Depends(rate_limit),
):
    try:
        response = await rag.generate(query=q)
        return response
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
