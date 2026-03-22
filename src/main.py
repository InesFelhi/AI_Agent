
"""
Main entry point for AndroMate RAG API.
"""

import uvicorn
from src.api.rag_api import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)