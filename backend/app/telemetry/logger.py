"""
Structured JSON Logger.

Person 5 owns this file.
Provides consistent JSON logging across the entire application.
"""

import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(name: str = "math_agent") -> logging.Logger:
    """Create a configured logger instance."""
    _logger = logging.getLogger(name)

    if _logger.handlers:
        return _logger

    _logger.setLevel(logging.DEBUG)

    # Console handler with JSON formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JSONFormatter())
    _logger.addHandler(handler)

    # Prevent propagation to root logger
    _logger.propagate = False

    return _logger


# Global logger instance
logger = setup_logger()
