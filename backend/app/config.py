from pydantic_settings import BaseSettings
from functools import lru_cache


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

    # Cache
    redis_url: str = "redis://localhost:6379"

    # Embedding (BGE-M3 - local, free)
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimensions: int = 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
