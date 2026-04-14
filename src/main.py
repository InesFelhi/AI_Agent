
"""
Main entry point for AndroMate APIs.
"""

import argparse
import uvicorn
from src.config import config


def parse_args():
    parser = argparse.ArgumentParser(description="Run the AndroMate API server.")
    parser.add_argument(
        "--app",
        choices=["rag", "chat"],
        default="rag",
        help="API app to run (default: rag)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    module = "src.api.rag_api" if args.app == "rag" else "src.api.chat_api"

    uvicorn.run(
        f"{module}:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD
    )