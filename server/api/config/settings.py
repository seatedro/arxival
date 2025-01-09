from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings, extra="allow"):
    ENV: str = "dev"
    ALLOWED_ORIGINS: List[str] = (
        ["http://localhost:3000", "https://www.arxival.xyz"]
        if ENV == "dev"
        else ["https://www.arxival.xyz", "https://s.arxival.xyz"]
    )
    CHROMADB_TOKEN: str = os.getenv("CHROMADB_TOKEN", "dummy")
    CHROMADB_SERVER: str = os.getenv("CHROMADB_SERVER", "http://localhost:8080")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
