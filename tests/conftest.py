"""
Pytest configuration and fixtures.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from rev_exporter.config import Config
from rev_exporter.client import RevAPIClient


@pytest.fixture
def mock_config():
    """Create a mock config with API keys."""
    config = Config()
    config.client_api_key = "test_client_key"
    config.user_api_key = "test_user_key"
    return config


@pytest.fixture
def mock_config_unconfigured(monkeypatch, tmp_path):
    """Create a mock config without API keys."""
    # Mock Path.cwd to prevent loading from docs/key.md
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    config = Config()
    config.api_key = None
    config.client_api_key = None
    config.user_api_key = None
    return config


@pytest.fixture
def sample_order_data():
    """Sample order data from API."""
    return {
        "order_number": "12345",
        "status": "Complete",
        "placed_on": "2024-01-15T10:30:00Z",
        "attachments": [
            {
                "id": "att_001",
                "name": "transcript.json",
                "type": "transcript",
                "download_uri": "https://example.com/download/att_001",
            },
            {
                "id": "att_002",
                "name": "audio.mp3",
                "type": "media",
                "download_uri": "https://example.com/download/att_002",
            },
        ],
    }


@pytest.fixture
def sample_orders_list_response():
    """Sample orders list API response."""
    return {
        "total_count": 2,
        "results_per_page": 50,
        "page": 0,
        "orders": [
            {
                "order_number": "12345",
                "status": "Complete",
                "placed_on": "2024-01-15T10:30:00Z",
            },
            {
                "order_number": "12346",
                "status": "In Progress",
                "placed_on": "2024-01-16T11:00:00Z",
            },
        ],
    }


@pytest.fixture
def sample_attachment_data():
    """Sample attachment metadata."""
    return {
        "id": "att_001",
        "name": "transcript.json",
        "type": "transcript",
        "download_uri": "https://example.com/download/att_001",
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_api_client(mock_config):
    """Create a mock API client."""
    client = RevAPIClient(config=mock_config)
    return client


@pytest.fixture
def mock_requests_response():
    """Create a mock requests Response object."""
    def _create_response(
        status_code=200,
        json_data=None,
        content=None,
        headers=None,
    ):
        response = Mock()
        response.status_code = status_code
        response.headers = headers or {}
        response.json.return_value = json_data or {}
        response.content = content or b""
        response.text = content.decode("utf-8") if content else ""
        response.raise_for_status = Mock()
        return response

    return _create_response

