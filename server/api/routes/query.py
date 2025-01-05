import json
from fastapi import APIRouter, HTTPException, Depends, Query
from rag.rag import RAGPipeline
from api.rate_limit import rate_limit
import logging
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
rag = RAGPipeline()


# @router.get("/query")
# async def query(
#     q: str = Query(..., description="Query string", min_length=1),
#     _: None = Depends(rate_limit),
# ):
#     try:
#         response = await rag.generate(query=q)
#         return response
#     except Exception as e:
#         logger.error(f"Query failed: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/stream")
async def stream_query(
    q: str = Query(..., description="Query string", min_length=1),
    _: None = Depends(rate_limit),
):
    async def event_generator():
        try:
            async for chunk in rag.generate(query=q):
                if chunk["type"] == "error":
                    yield {"event": "error", "data": json.dumps(chunk["data"])}
                    break
                else:
                    yield {"event": chunk["type"], "data": json.dumps(chunk["data"])}
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(event_generator(), ping=1, headers={"Cache-Control": "no-cache", 'X-Accel-Buffering': 'no'})
