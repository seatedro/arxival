from fastapi import APIRouter, HTTPException, Depends
from api.rate_limit import rate_limit
from ingestion.filter import ProcessedPaperTracker
import os
import json
import logging
from api.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")
paper_tracker = ProcessedPaperTracker(
    chromadb_host=settings.CHROMADB_SERVER, chromadb_token=settings.CHROMADB_TOKEN
)


@router.get("/stats")
async def get_stats(_: None = Depends(rate_limit)):
    try:
        processed_papers = paper_tracker.get_processed_papers()

        # Get error stats if they exist
        error_stats = {"total": 0, "by_stage": {}}
        if os.path.exists("logs/ingestion_errors.jsonl"):
            with open("logs/ingestion_errors.jsonl") as f:
                for line in f:
                    error = json.loads(line)
                    error_stats["total"] += 1
                    stage = error["stage"]
                    error_stats["by_stage"][stage] = (
                        error_stats["by_stage"].get(stage, 0) + 1
                    )

        return {"total_papers": len(processed_papers), "errors": error_stats}
    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
