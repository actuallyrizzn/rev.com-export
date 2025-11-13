"""
Unit tests for config module.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from rev_exporter.config import Config


class TestConfig:
    """Test Config class."""

    def test_load_from_env(self, tmp_path, monkeypatch):
        """Test loading credentials from environment variables."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "env_client_key")
        monkeypatch.setenv("REV_USER_API_KEY", "env_user_key")

        config = Config()
        assert config.client_api_key == "env_client_key"
        assert config.user_api_key == "env_user_key"
        assert config.is_configured() is True

    def test_load_from_file(self, tmp_path):
        """Test loading credentials from config file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "client_api_key": "file_client_key",
            "user_api_key": "file_user_key",
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(config_file=config_file)
        assert config.client_api_key == "file_client_key"
        assert config.user_api_key == "file_user_key"
        assert config.is_configured() is True

    def test_env_priority_over_file(self, tmp_path, monkeypatch):
        """Test that ENV vars take priority over config file."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "env_key")
        monkeypatch.setenv("REV_USER_API_KEY", "env_user")

        config_file = tmp_path / "config.json"
        config_data = {
            "client_api_key": "file_key",
            "user_api_key": "file_user",
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(config_file=config_file)
        assert config.client_api_key == "env_key"
        assert config.user_api_key == "env_user"

    def test_not_configured(self):
        """Test unconfigured state."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.is_configured() is False
            assert config.client_api_key is None
            assert config.user_api_key is None

    def test_get_auth_header(self, mock_config):
        """Test getting authorization header."""
        header = mock_config.get_auth_header()
        assert header == "Rev test_client_key:test_user_key"

    def test_get_auth_header_unconfigured(self, mock_config_unconfigured):
        """Test getting auth header when not configured."""
        with pytest.raises(ValueError, match="API credentials not configured"):
            mock_config_unconfigured.get_auth_header()

    def test_to_dict(self, mock_config):
        """Test converting config to dict."""
        result = mock_config.to_dict()
        assert result["client_api_key_configured"] is True
        assert result["user_api_key_configured"] is True

    def test_find_config_file_current_dir(self, tmp_path, monkeypatch):
        """Test finding config file in current directory."""
        monkeypatch.chdir(tmp_path)
        config_file = tmp_path / "config.json"
        config_file.write_text('{"client_api_key": "test", "user_api_key": "test"}')

        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            assert config.config_file == config_file

    def test_invalid_config_file(self, tmp_path):
        """Test handling invalid config file."""
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json{")

        with patch.dict(os.environ, {}, clear=True):
            config = Config(config_file=config_file)
            assert config.is_configured() is False

