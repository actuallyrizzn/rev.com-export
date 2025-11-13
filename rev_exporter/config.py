"""
Configuration management for Rev Exporter.

Loads API credentials from environment variables (preferred) or config file.
Priority: ENV vars > config file
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Rev Exporter."""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to config file. If None, looks for
                        config.json in current directory or user home.
        """
        self.client_api_key: Optional[str] = None
        self.user_api_key: Optional[str] = None
        self.config_file = config_file or self._find_config_file()
        self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find config file in common locations."""
        # Check current directory
        current_dir = Path.cwd() / "config.json"
        if current_dir.exists():
            return current_dir

        # Check user home directory
        home_dir = Path.home() / ".rev-exporter" / "config.json"
        if home_dir.exists():
            return home_dir

        return None

    def _load_from_env(self) -> bool:
        """Load credentials from environment variables."""
        client_key = os.getenv("REV_CLIENT_API_KEY")
        user_key = os.getenv("REV_USER_API_KEY")

        if client_key and user_key:
            self.client_api_key = client_key
            self.user_api_key = user_key
            logger.debug("Loaded credentials from environment variables")
            return True

        return False

    def _load_from_file(self) -> bool:
        """Load credentials from config file."""
        if not self.config_file or not self.config_file.exists():
            return False

        try:
            with open(self.config_file, "r") as f:
                config_data = json.load(f)

            self.client_api_key = config_data.get("client_api_key")
            self.user_api_key = config_data.get("user_api_key")

            if self.client_api_key and self.user_api_key:
                logger.debug(f"Loaded credentials from config file: {self.config_file}")
                return True
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config file {self.config_file}: {e}")

        return False

    def _load_config(self) -> None:
        """Load configuration with priority: ENV vars > config file."""
        # Try environment variables first
        if self._load_from_env():
            return

        # Fallback to config file
        if self._load_from_file():
            return

        # No credentials found
        logger.warning(
            "No credentials found. Set REV_CLIENT_API_KEY and REV_USER_API_KEY "
            "environment variables or create a config file."
        )

    def is_configured(self) -> bool:
        """Check if both API keys are configured."""
        return bool(self.client_api_key and self.user_api_key)

    def get_auth_header(self) -> str:
        """
        Get the Authorization header value for Rev API.

        Returns:
            Authorization header value in format: "Rev CLIENT_API_KEY:USER_API_KEY"
        """
        if not self.is_configured():
            raise ValueError("API credentials not configured")

        return f"Rev {self.client_api_key}:{self.user_api_key}"

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary (without sensitive data)."""
        return {
            "client_api_key_configured": bool(self.client_api_key),
            "user_api_key_configured": bool(self.user_api_key),
            "config_file": str(self.config_file) if self.config_file else None,
        }

