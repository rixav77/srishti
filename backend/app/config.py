from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache

# .env lives at the repo root (one level above backend/)
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    # API
    app_name: str = "Srishti"
    debug: bool = True

    # LLM (Groq - free)
    groq_api_key: str = ""
    default_model: str = "llama-3.3-70b-versatile"
    fast_model: str = "llama-3.1-8b-instant"

    # Database
    supabase_url: str = ""
    supabase_key: str = ""
    database_url: str = ""

    # Vector DB
    pinecone_api_key: str = ""
    pinecone_index_name: str = "srishti"

    # Live tools
    exa_api_key: str = ""

    # Cache
    redis_url: str = "redis://localhost:6379"

    # Embedding (BGE-M3 - local, free)
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024

    model_config = {"env_file": str(_ENV_FILE), "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
