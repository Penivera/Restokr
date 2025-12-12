"""
Logging configuration for ReStockr API.

Provides uvicorn-style logging with colored output and proper formatting.
"""

import logging
import sys
from typing import Any

# ANSI color codes for terminal output
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
}

# Emoji prefixes for different log levels
EMOJI = {
    "DEBUG": "🔍",
    "INFO": "ℹ️ ",
    "WARNING": "⚠️ ",
    "ERROR": "❌",
    "CRITICAL": "🔥",
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis matching uvicorn style."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and emojis."""
        # Add color to level name
        levelname = record.levelname
        if levelname in COLORS:
            colored_levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
            record.levelname = colored_levelname

        # Format the message
        formatted = super().format(record)

        # Add emoji prefix
        if levelname in EMOJI:
            formatted = f"{EMOJI[levelname]} {formatted}"

        return formatted


class UvicornStyleFormatter(logging.Formatter):
    """Formatter that matches uvicorn's logging style."""

    FORMATS = {
        logging.DEBUG: "\033[36mDEBUG\033[0m:    %(message)s",
        logging.INFO: "\033[32mINFO\033[0m:     %(message)s",
        logging.WARNING: "\033[33mWARNING\033[0m:  %(message)s",
        logging.ERROR: "\033[31mERROR\033[0m:    %(message)s",
        logging.CRITICAL: "\033[35mCRITICAL\033[0m: %(message)s",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in uvicorn style."""
        log_fmt = self.FORMATS.get(record.levelno, "%(levelname)s: %(message)s")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string to logging level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(UvicornStyleFormatter())

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=[console_handler],
        force=True,
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
