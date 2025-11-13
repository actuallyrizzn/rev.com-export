"""
Logging configuration for Rev Exporter.

Sets up structured logging with INFO/WARN/ERROR levels.
Ensures API keys are never logged.
"""

import logging
import sys
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter to prevent logging of sensitive data like API keys."""

    SENSITIVE_PATTERNS = [
        "api_key",
        "api-key",
        "apikey",
        "authorization",
        "auth",
        "password",
        "token",
        "secret",
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to redact sensitive information."""
        # Redact sensitive patterns in log messages
        message = str(record.getMessage())
        for pattern in self.SENSITIVE_PATTERNS:
            # Simple redaction - replace any occurrence with [REDACTED]
            if pattern.lower() in message.lower():
                # Don't log messages that might contain sensitive data
                return False

        return True


def setup_logging(
    level: int = logging.INFO,
    debug: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Set up logging configuration.

    Args:
        level: Logging level (default: INFO)
        debug: If True, enable debug logging
        log_file: Optional path to log file
    """
    if debug:
        level = logging.DEBUG

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

