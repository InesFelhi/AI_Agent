"""
Configuration module for AI Agent RAG pipeline.

Centralizes all application settings including:
- API configuration (host, port, title, version)
- Qdrant vector database settings
- Embedding model configuration
- Text processing parameters (chunking, overlap)

Loads environment variables from .env file (if exists) using python-dotenv.
"""

import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not installed, continue without .env support
    pass


class Config:
    """Application configuration."""
    
    # ==================== API Configuration ====================
    API_TITLE: str = "AndroMate RAG API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_RELOAD: bool = os.getenv("API_RELOAD", "True").lower() == "true"
    
    # ==================== Qdrant Vector Store Configuration ====================
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "andromate_docs")
    QDRANT_VECTOR_SIZE: int = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
    
    # ==================== Embedding Model Configuration ====================
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    EMBEDDING_CACHE_DIR: Optional[str] = os.getenv("EMBEDDING_CACHE_DIR", None)
    
    # ==================== Text Processing Configuration ====================
    CHUNK_MAX_SIZE: int = int(os.getenv("CHUNK_MAX_SIZE", "200"))  # words
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))     # words
    
    # ==================== File Upload Configuration ====================
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    ALLOWED_EXTENSIONS: tuple = (".md", ".txt")
    
    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_MAX_BYTES: int = int(os.getenv("LOG_MAX_BYTES", "5242880"))  # 5MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "3"))

    # ==================== Security Configuration ====================
    API_KEY: str = os.getenv("API_KEY", "your-default-api-key")
    API_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
    CORS_ALLOW_ORIGINS: tuple = tuple(os.getenv("CORS_ALLOW_ORIGINS", "*").split(","))

    @classmethod
    def to_dict(cls) -> dict:
        """Return all configuration as dictionary."""
        return {
            key: getattr(cls, key)
            for key in dir(cls)
            if not key.startswith("_") and key.isupper()
        }


# Export config instance
config = Config()
