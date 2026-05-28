
"""
Main entry point for AndroMate APIs.
"""

import argparse
import sys
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
    # Validate configuration at startup
    try:
        config.validate()
        print("[OK] Configuration validated successfully")
    except ValueError as e:
        print(f"[ERROR] Configuration validation failed:\n{str(e)}", file=sys.stderr)
        sys.exit(1)
    
    args = parse_args()
    module = "src.api.rag_api" if args.app == "rag" else "src.api.chat_api"

    uvicorn.run(
        f"{module}:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_RELOAD
    )