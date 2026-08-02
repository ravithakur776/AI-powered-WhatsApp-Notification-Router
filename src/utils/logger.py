"""Structured logger for system telemetry, trace logs, and performance monitoring."""

import sys
import json
from loguru import logger
from config.settings import LOG_DIR, LOG_LEVEL

logger.remove()

# Console logger with rich formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=LOG_LEVEL,
    colorize=True,
)

# File logger writing JSON log entries
def serialize_log(record):
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "extra": record["extra"]
    }
    return json.dumps(log_entry) + "\n"

logger.add(
    LOG_DIR / "router_audit.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    serialize=True
)

__all__ = ["logger"]
