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
        # Test single API key format
        monkeypatch.setenv("REV_API_KEY", "env_api_key")
        monkeypatch.delenv("REV_CLIENT_API_KEY", raising=False)
        monkeypatch.delenv("REV_USER_API_KEY", raising=False)

        config = Config()
        assert config.api_key == "env_api_key"
        assert config.is_configured() is True
        
        # Test two-key format (backward compatibility)
        monkeypatch.delenv("REV_API_KEY", raising=False)
        monkeypatch.setenv("REV_CLIENT_API_KEY", "env_client_key")
        monkeypatch.setenv("REV_USER_API_KEY", "env_user_key")

        config2 = Config()
        assert config2.client_api_key == "env_client_key"
        assert config2.user_api_key == "env_user_key"
        assert config2.is_configured() is True

    def test_load_from_file(self, tmp_path, monkeypatch):
        """Test loading credentials from config file."""
        # Mock Path.cwd to return tmp_path so key file doesn't exist
        original_cwd = Path.cwd
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
        
        try:
            # Test single API key format
            config_file = tmp_path / "config.json"
            config_data = {"api_key": "file_api_key"}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            config = Config(config_file=config_file)
            # Config file should take priority, but if key file exists it may load first
            # So we check that _load_from_file works correctly
            config.api_key = None
            result = config._load_from_file()
            assert result is True
            assert config.api_key == "file_api_key"
            
            # Test two-key format (backward compatibility)
            config_data2 = {
                "client_api_key": "file_client_key",
                "user_api_key": "file_user_key",
            }
            with open(config_file, "w") as f:
                json.dump(config_data2, f)

            config2 = Config(config_file=config_file)
            config2.client_api_key = None
            config2.user_api_key = None
            result2 = config2._load_from_file()
            assert result2 is True
            assert config2.client_api_key == "file_client_key"
            assert config2.user_api_key == "file_user_key"
        finally:
            monkeypatch.setattr("pathlib.Path.cwd", original_cwd)

    def test_env_priority_over_file(self, tmp_path, monkeypatch):
        """Test that ENV vars take priority over config file."""
        monkeypatch.setenv("REV_API_KEY", "env_key")
        monkeypatch.delenv("REV_CLIENT_API_KEY", raising=False)
        monkeypatch.delenv("REV_USER_API_KEY", raising=False)

        config_file = tmp_path / "config.json"
        config_data = {"api_key": "file_key"}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = Config(config_file=config_file)
        assert config.api_key == "env_key"

    def test_not_configured(self, tmp_path, monkeypatch):
        """Test unconfigured state."""
        monkeypatch.chdir(tmp_path)
        with patch.dict(os.environ, {}, clear=True):
            # Mock Path.home() to avoid home directory issues in test environment
            with patch("rev_exporter.config.Path.home", return_value=tmp_path):
                config = Config()
                assert config.is_configured() is False
                assert config.client_api_key is None
                assert config.user_api_key is None

    def test_get_auth_header(self, mock_config):
        """Test getting authorization header."""
        # Test with single API key
        mock_config.api_key = "test_api_key"
        mock_config.client_api_key = None
        mock_config.user_api_key = None
        header = mock_config.get_auth_header()
        assert header == "Rev test_api_key:test_api_key"
        
        # Test with two-key format
        mock_config.api_key = None
        mock_config.client_api_key = "test_client_key"
        mock_config.user_api_key = "test_user_key"
        header2 = mock_config.get_auth_header()
        assert header2 == "Rev test_client_key:test_user_key"

    def test_get_auth_header_unconfigured(self, tmp_path, monkeypatch):
        """Test getting auth header when not configured."""
        # Mock key file to prevent fallback
        monkeypatch.setattr("rev_exporter.config.Path.cwd", lambda: tmp_path)
        monkeypatch.delenv("REV_API_KEY", raising=False)
        monkeypatch.delenv("REV_CLIENT_API_KEY", raising=False)
        monkeypatch.delenv("REV_USER_API_KEY", raising=False)
        
        config = Config()
        with pytest.raises(ValueError, match="API credentials not configured"):
            config.get_auth_header()

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

    def test_invalid_config_file(self, tmp_path, monkeypatch):
        """Test handling invalid config file."""
        # Mock key file to prevent fallback
        monkeypatch.setattr("rev_exporter.config.Path.cwd", lambda: tmp_path)
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json{")

        with patch.dict(os.environ, {}, clear=True):
            config = Config(config_file=config_file)
            assert config.is_configured() is False

    def test_config_file_missing_keys(self, tmp_path, monkeypatch):
        """Test config file with missing keys."""
        # Mock key file to prevent fallback
        monkeypatch.setattr("rev_exporter.config.Path.cwd", lambda: tmp_path)
        config_file = tmp_path / "config.json"
        config_file.write_text('{"client_api_key": "only_client"}')

        with patch.dict(os.environ, {}, clear=True):
            config = Config(config_file=config_file)
            assert config.is_configured() is False

    def test_config_file_io_error(self, tmp_path, monkeypatch):
        """Test handling IO errors when reading config file."""
        # Mock key file to prevent fallback
        monkeypatch.setattr("rev_exporter.config.Path.cwd", lambda: tmp_path)
        config_file = tmp_path / "config.json"
        config_file.write_text('{"client_api_key": "test", "user_api_key": "test"}')

        # Mock open to raise IOError for config file only
        original_open = open
        def mock_open(*args, **kwargs):
            if "config.json" in str(args[0]):
                raise IOError("Permission denied")
            return original_open(*args, **kwargs)

        with patch.dict(os.environ, {}, clear=True), \
             patch("builtins.open", side_effect=mock_open):
            config = Config(config_file=config_file)
            assert config.is_configured() is False

    def test_find_config_file_home_dir(self, tmp_path, monkeypatch):
        """Test finding config file in home directory."""
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / ".rev-exporter"
        home_dir.mkdir()
        config_file = home_dir / "config.json"
        config_file.write_text('{"client_api_key": "test", "user_api_key": "test"}')

        with patch.dict(os.environ, {}, clear=True), \
             patch("rev_exporter.config.Path.home", return_value=tmp_path):
            config = Config()
            assert config.config_file == config_file

    def test_load_from_key_file_io_error(self, tmp_path, monkeypatch):
        """Test loading from key file with IOError."""
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
        key_file = tmp_path / "docs" / "key.md"
        key_file.parent.mkdir(parents=True)
        key_file.write_text("test_key")
        
        with patch.dict(os.environ, {}, clear=True), \
             patch("rev_exporter.config.Path.home", return_value=tmp_path), \
             patch.object(Path, "read_text", side_effect=IOError("Permission denied")):
            config = Config()
            assert config.is_configured() is False

    def test_load_from_key_file_unicode_error(self, tmp_path, monkeypatch):
        """Test loading from key file with UnicodeDecodeError."""
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
        key_file = tmp_path / "docs" / "key.md"
        key_file.parent.mkdir(parents=True)
        key_file.write_text("test_key")
        
        with patch.dict(os.environ, {}, clear=True), \
             patch("rev_exporter.config.Path.home", return_value=tmp_path), \
             patch.object(Path, "read_text", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            config = Config()
            assert config.is_configured() is False

