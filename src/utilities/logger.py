"""
logger.py

Centralized and module-specific logging configuration for the application.

This module provides:
- A reusable logger factory for all application modules.
- Automatic creation of log files per module in the 'logs' directory.
- Console output for real-time debugging.
- Rotating file logging to prevent unlimited file growth (production-safe).
- UTF-8 encoding support for proper international characters.
- Structured log format including timestamp, log level, module name, and message.

Usage Example:
----------------
from logger import get_module_logger

# Create logger for Document Cleaner
doc_cleaner_logger = get_module_logger("document_cleaner")
doc_cleaner_logger.debug("Document cleaning started")
"""

from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Default log directory
LOG_DIR: Path = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True) 


def get_module_logger(
    name: str,
    log_file: str | None = None,
    level: int = logging.DEBUG,
    max_bytes: int = 5 * 1024 * 1024,  
    backup_count: int = 5
) -> logging.Logger:
    """
    Creates and returns a configured logger instance for a specific module.

    This logger writes logs to both a file and the console, with UTF-8 support,
    and uses a RotatingFileHandler to prevent logs from growing indefinitely.

    Args:
        name (str): Name of the logger (typically the module name).
        log_file (str | None): Optional log file name. Defaults to '{name}.log' in 'logs/' directory.
        level (int): Logging level (e.g., logging.DEBUG, logging.INFO).
        max_bytes (int): Maximum size in bytes before rotating the log file.
        backup_count (int): Number of backup files to keep when rotating.

    Returns:
        logging.Logger: Configured logger instance.
    """
    if log_file is None:
        log_file_path = LOG_DIR / f"{name}.log"
    else:
        log_file_path = LOG_DIR / log_file

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        # Formatter for both console and file
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Rotating file handler
        file_handler = RotatingFileHandler(
            filename=log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.encoding = "utf-8"
        logger.addHandler(console_handler)

    return logger
