
"""
Main entry point for AndroMate RAG API.
"""

import uvicorn
from src.api.rag_api import app
from src.config import config

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD
    )