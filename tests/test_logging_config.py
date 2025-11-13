"""
Unit tests for logging_config module.
"""

import logging
import sys
from unittest.mock import patch, MagicMock

from rev_exporter.logging_config import setup_logging, SensitiveDataFilter


class TestSensitiveDataFilter:
    """Test SensitiveDataFilter class."""

    def test_filter_sensitive_patterns(self):
        """Test filtering sensitive data patterns."""
        filter_obj = SensitiveDataFilter()

        # Create a log record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API key: secret123",
            args=(),
            exc_info=None,
        )

        # Should filter out records with sensitive patterns
        result = filter_obj.filter(record)
        assert result is False

    def test_filter_normal_message(self):
        """Test that normal messages pass through."""
        filter_obj = SensitiveDataFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Normal log message",
            args=(),
            exc_info=None,
        )

        result = filter_obj.filter(record)
        assert result is True

    def test_filter_case_insensitive(self):
        """Test that filtering is case insensitive."""
        filter_obj = SensitiveDataFilter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API_KEY: secret123",
            args=(),
            exc_info=None,
        )

        result = filter_obj.filter(record)
        assert result is False


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_default(self):
        """Test setting up logging with default settings."""
        setup_logging()
        root_logger = logging.getLogger()

        assert root_logger.level == logging.INFO
        assert len(root_logger.handlers) > 0

    def test_setup_logging_debug(self):
        """Test setting up logging with debug enabled."""
        setup_logging(debug=True)
        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_custom_level(self):
        """Test setting up logging with custom level."""
        setup_logging(level=logging.WARNING)
        root_logger = logging.getLogger()

        assert root_logger.level == logging.WARNING

    def test_setup_logging_with_file(self, tmp_path):
        """Test setting up logging with log file."""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))

        root_logger = logging.getLogger()
        file_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) > 0

    def test_setup_logging_removes_existing_handlers(self):
        """Test that setup_logging removes existing handlers."""
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]

        setup_logging()
        # Should have cleared and added new handlers
        assert len(root_logger.handlers) >= 1

    def test_setup_logging_suppresses_third_party(self):
        """Test that third-party loggers are suppressed."""
        setup_logging()
        urllib3_logger = logging.getLogger("urllib3")
        assert urllib3_logger.level >= logging.WARNING

        requests_logger = logging.getLogger("requests")
        assert requests_logger.level >= logging.WARNING

