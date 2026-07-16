"""
Configuration settings for the delivery assurance copilot backend.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str
    
    # LangSmith
    langchain_api_key: Optional[str] = None
    langchain_tracing_v2: bool = False
    langchain_project: str = "delivery-assurance-copilot"
    
    # Database
    database_url: str = "postgresql+asyncpg://copilot:copilot123@localhost:5432/copilotdb"
    
    # ChromaDB
    chroma_persist_dir: str = "/data/chroma"
    
    # Embedding Model
    embed_model: str = "all-MiniLM-L6-v2"
    
    # Document Chunking
    chunk_size: int = 512
    chunk_overlap: int = 50
    
    # RAG Retrieval
    top_k_retrieval: int = 6
    
    # Environment
    environment: str = "development"
    
    # Jira Addon (Credentials from environment)
    jira_addon_enabled: bool = False
    jira_username: Optional[str] = None
    jira_api_token: Optional[str] = None
    encryption_key: Optional[str] = None
    
    # App
    app_name: str = "Delivery Assurance Copilot"
    app_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
