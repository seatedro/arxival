import asyncio
import json
from fastapi import APIRouter, HTTPException, Depends, Query
from rag.rag import RAGPipeline
from api.rate_limit import rate_limit
import logging
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
rag = RAGPipeline()


@router.get("/sse")
async def sse_endpoint():
    async def event_generator():
        for i in range(5):
            yield {"data": f"Message {i}"}
            await asyncio.sleep(1)

    return EventSourceResponse(event_generator())


@router.get("/query/stream")
async def stream_query(
    q: str = Query(..., description="Query string", min_length=1),
    _: None = Depends(rate_limit),
):
    async def event_generator():
        try:
            async for chunk in rag.generate(query=q):
                if chunk["event"] == "error":
                    yield {"event": "error", "data": chunk["data"]}
                    break
                else:
                    yield {"event": chunk["event"], "data": chunk["data"]}
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            yield {"event": "error", "data": json.dumps({"message": str(e)})}

    return EventSourceResponse(
        event_generator(),
    )
