"""
Unit tests for client module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, HTTPError
from requests import Response

from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.config import Config


class TestRevAPIClient:
    """Test RevAPIClient class."""

    def test_init(self, mock_config):
        """Test client initialization."""
        client = RevAPIClient(config=mock_config)
        assert client.config == mock_config
        assert client.BASE_URL == "https://www.rev.com/api/v1"
        assert "Authorization" in client.session.headers

    def test_init_unconfigured(self, mock_config_unconfigured):
        """Test client initialization without config."""
        client = RevAPIClient(config=mock_config_unconfigured)
        assert client.config == mock_config_unconfigured

    def test_get_json_response(self, mock_config, mock_requests_response):
        """Test GET request with JSON response."""
        client = RevAPIClient(config=mock_config)
        json_data = {"key": "value"}

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(json_data=json_data)
            mock_request.return_value = mock_response

            result = client.get("/test")
            assert result == json_data

    def test_get_binary_response(self, mock_config, mock_requests_response):
        """Test GET request with binary response."""
        client = RevAPIClient(config=mock_config)
        binary_data = b"binary content"

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(content=binary_data)
            mock_request.return_value = mock_response

            result = client.get("/test", stream=True)
            assert result == binary_data

    def test_get_with_params(self, mock_config, mock_requests_response):
        """Test GET request with parameters."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(json_data={})
            mock_request.return_value = mock_response

            client.get("/test", params={"page": 1, "limit": 10})
            call_args = mock_request.call_args
            assert call_args[1]["params"] == {"page": 1, "limit": 10}

    def test_get_request_exception(self, mock_config):
        """Test GET request with RequestException."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = RequestException("Network error")

            with pytest.raises(RevAPIError, match="API request failed"):
                client.get("/test")

    def test_get_http_error(self, mock_config, mock_requests_response):
        """Test GET request with HTTP error."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(status_code=404)
            mock_response.raise_for_status.side_effect = HTTPError("Not found")
            mock_request.return_value = mock_response

            with pytest.raises(RevAPIError):
                client.get("/test")

    def test_post_request(self, mock_config, mock_requests_response):
        """Test POST request."""
        client = RevAPIClient(config=mock_config)
        json_data = {"result": "success"}

        with patch.object(client.session, "post") as mock_post:
            mock_response = mock_requests_response(json_data=json_data)
            mock_post.return_value = mock_response

            result = client.post("/test", json_data={"key": "value"})
            assert result == json_data

    def test_post_request_exception(self, mock_config):
        """Test POST request with exception."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "post") as mock_post:
            mock_post.side_effect = RequestException("Error")

            with pytest.raises(RevAPIError):
                client.post("/test", json_data={})

    def test_parse_json_response_invalid(self, mock_config):
        """Test parsing invalid JSON response."""
        client = RevAPIClient(config=mock_config)
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with pytest.raises(RevAPIError, match="Invalid JSON response"):
            client._parse_json_response(mock_response)

    def test_test_connection_success(self, mock_config, mock_requests_response):
        """Test successful connection test."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client, "get") as mock_get:
            mock_get.return_value = {"orders": []}
            result = client.test_connection()
            assert result is True

    def test_test_connection_failure(self, mock_config):
        """Test failed connection test."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client, "get") as mock_get:
            mock_get.side_effect = RevAPIError("Connection failed")
            result = client.test_connection()
            assert result is False

    def test_test_connection_unconfigured(self, mock_config_unconfigured):
        """Test connection test when not configured."""
        client = RevAPIClient(config=mock_config_unconfigured)
        result = client.test_connection()
        assert result is False

    def test_make_request_with_headers(self, mock_config, mock_requests_response):
        """Test _make_request with custom headers."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(json_data={})
            mock_request.return_value = mock_response

            client._make_request("GET", "/test", headers={"Custom-Header": "value"})
            call_args = mock_request.call_args
            assert call_args[1]["headers"]["Custom-Header"] == "value"

    def test_make_request_with_auth_header(self, mock_config, mock_requests_response):
        """Test _make_request adds auth header when missing."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "request") as mock_request:
            mock_response = mock_requests_response(json_data={})
            mock_request.return_value = mock_response

            client._make_request("GET", "/test", headers={})
            call_args = mock_request.call_args
            assert "Authorization" in call_args[1]["headers"]

    def test_post_with_custom_headers(self, mock_config, mock_requests_response):
        """Test POST with custom headers."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "post") as mock_post:
            mock_response = mock_requests_response(json_data={})
            mock_post.return_value = mock_response

            client.post("/test", headers={"Custom-Header": "value"}, json_data={})
            call_args = mock_post.call_args
            assert call_args[1]["headers"]["Custom-Header"] == "value"

    def test_post_with_existing_auth(self, mock_config, mock_requests_response):
        """Test POST with existing auth header."""
        client = RevAPIClient(config=mock_config)

        with patch.object(client.session, "post") as mock_post:
            mock_response = mock_requests_response(json_data={})
            mock_post.return_value = mock_response

            client.post("/test", headers={"Authorization": "existing"}, json_data={})
            call_args = mock_post.call_args
            assert call_args[1]["headers"]["Authorization"] == "existing"

