from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import os

from api.routes import query, stats
from api.models import HealthResponse
from api.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ArXival API")

print(settings.ALLOWED_ORIGINS, settings.ENV)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)

    error_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "message": str(exc)
            if settings.ENV == "dev"
            else "An unexpected error occurred",
        },
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        # Check last successful ingestion
        last_ingest = None
        last_run_file = os.path.join("logs", "last_successful_run")

        if os.path.exists(last_run_file):
            with open(last_run_file) as f:
                last_ingest = f.read().strip()

        return {"status": "healthy", "env": settings.ENV, "last_ingest": last_ingest}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


app.include_router(query.router)
app.include_router(stats.router)
