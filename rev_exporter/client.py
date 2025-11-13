"""
Rev.com API Client.

Handles authentication, requests, retries, and response parsing.
"""

import time
import logging
from typing import Optional, Dict, Any, Union
from requests import Session, Response, RequestException
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from rev_exporter.config import Config

logger = logging.getLogger(__name__)


class RevAPIError(Exception):
    """Base exception for Rev API errors."""

    pass


class RevAPIClient:
    """Client for interacting with the Rev.com API."""

    BASE_URL = "https://www.rev.com/api/v1"

    def __init__(
        self,
        config: Optional[Config] = None,
        max_retries: int = 3,
        retry_backoff_factor: float = 1.0,
    ):
        """
        Initialize the Rev API client.

        Args:
            config: Configuration object with API keys. If None, creates new Config.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_backoff_factor: Backoff factor for exponential retry delays.
        """
        self.config = config or Config()
        self.max_retries = max_retries
        self.retry_backoff_factor = retry_backoff_factor

        # Create session with retry strategy
        self.session = Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        if self.config.is_configured():
            self.session.headers.update(
                {"Authorization": self.config.get_auth_header()}
            )
        else:
            logger.warning("API credentials not configured")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Response:
        """
        Make an HTTP request to the Rev API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/orders")
            params: Query parameters
            headers: Additional headers
            stream: If True, stream the response

        Returns:
            Response object

        Raises:
            RevAPIError: If the request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        # Merge headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # Ensure auth header is set
        if not request_headers.get("Authorization") and self.config.is_configured():
            request_headers["Authorization"] = self.config.get_auth_header()

        logger.debug(f"Making {method} request to {url}")

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                headers=request_headers,
                stream=stream,
                timeout=30,
            )
            response.raise_for_status()
            return response
        except RequestException as e:
            logger.error(f"Request failed: {e}")
            raise RevAPIError(f"API request failed: {e}") from e

    def _parse_json_response(self, response: Response) -> Dict[str, Any]:
        """
        Parse JSON response.

        Args:
            response: Response object

        Returns:
            Parsed JSON data

        Raises:
            RevAPIError: If response is not valid JSON
        """
        try:
            return response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise RevAPIError(f"Invalid JSON response: {e}") from e

    def _parse_binary_response(self, response: Response) -> bytes:
        """
        Parse binary response.

        Args:
            response: Response object

        Returns:
            Binary data
        """
        return response.content

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Union[Dict[str, Any], bytes]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            stream: If True, return binary data; if False, parse as JSON

        Returns:
            JSON dict or binary data depending on stream parameter
        """
        response = self._make_request("GET", endpoint, params=params, headers=headers, stream=stream)
        if stream:
            return self._parse_binary_response(response)
        return self._parse_json_response(response)

    def post(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            json_data: JSON body data

        Returns:
            Parsed JSON response
        """
        url = f"{self.BASE_URL}{endpoint}"
        request_headers = {}
        if headers:
            request_headers.update(headers)

        if not request_headers.get("Authorization") and self.config.is_configured():
            request_headers["Authorization"] = self.config.get_auth_header()

        logger.debug(f"Making POST request to {url}")

        try:
            response = self.session.post(
                url=url,
                params=params,
                headers=request_headers,
                json=json_data,
                timeout=30,
            )
            response.raise_for_status()
            return self._parse_json_response(response)
        except RequestException as e:
            logger.error(f"POST request failed: {e}")
            raise RevAPIError(f"API request failed: {e}") from e

    def test_connection(self) -> bool:
        """
        Test the API connection by making a minimal request.

        Returns:
            True if connection successful, False otherwise
        """
        if not self.config.is_configured():
            logger.error("API credentials not configured")
            return False

        try:
            # Make minimal request to test connection
            response = self.get("/orders", params={"page": 0, "results_per_page": 1})
            logger.info("Connection test successful")
            return True
        except RevAPIError as e:
            logger.error(f"Connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False

