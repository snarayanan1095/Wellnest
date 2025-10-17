import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging in JSON format
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)

class StructuredLogger:
    """
    Wrapper class for structured logging
    """
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def log(self, level: int, message: str, **kwargs):
        """Log with additional structured fields"""
        extra = {"extra_fields": kwargs}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs):
        self.log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.log(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.log(logging.CRITICAL, message, **kwargs)

def setup_logging(level: str = "INFO", use_json: bool = True):
    """
    Setup application logging

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON structured logging
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)
