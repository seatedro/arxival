from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    status: str
    env: str
    version: str = "0.1.0"
    last_ingest: Optional[str]
