"""
Integration tests for Rev Exporter.

These tests require real API credentials to be set via environment variables.
Tests are skipped if credentials are not available.
"""

import os
import pytest
from pathlib import Path

from rev_exporter.config import Config
from rev_exporter.client import RevAPIClient
from rev_exporter.orders import OrderManager
from rev_exporter.attachments import AttachmentManager


# Skip all integration tests if credentials not available
pytestmark = pytest.mark.skipif(
    not (
        os.getenv("REV_CLIENT_API_KEY") and os.getenv("REV_USER_API_KEY")
    ),
    reason="Integration tests require REV_CLIENT_API_KEY and REV_USER_API_KEY",
)


class TestIntegration:
    """Integration tests with real API."""

    @pytest.fixture
    def config(self):
        """Create config from environment."""
        return Config()

    @pytest.fixture
    def client(self, config):
        """Create API client."""
        return RevAPIClient(config=config)

    @pytest.fixture
    def order_manager(self, client):
        """Create order manager."""
        return OrderManager(client)

    @pytest.fixture
    def attachment_manager(self, client):
        """Create attachment manager."""
        return AttachmentManager(client)

    def test_connection(self, client):
        """Test API connection."""
        result = client.test_connection()
        assert result is True

    def test_list_orders(self, order_manager):
        """Test listing orders."""
        response = order_manager.list_orders(page=0, results_per_page=1)
        assert "orders" in response
        assert isinstance(response["orders"], list)

    def test_get_all_orders(self, order_manager):
        """Test getting all orders (limited to first page for speed)."""
        # Just test that it works, don't fetch all orders
        orders = order_manager.get_all_orders(results_per_page=1)
        assert isinstance(orders, list)
        # If there are orders, verify structure
        if orders:
            order = orders[0]
            assert hasattr(order, "order_number")
            assert hasattr(order, "status")

    def test_get_order_details(self, order_manager):
        """Test getting order details."""
        # First get a list of orders
        response = order_manager.list_orders(page=0, results_per_page=1)
        if response.get("orders"):
            order_number = response["orders"][0]["order_number"]
            order = order_manager.get_order_details(order_number)
            assert order.order_number == order_number
            assert hasattr(order, "attachments")

    def test_filter_completed_orders(self, order_manager):
        """Test filtering completed orders."""
        response = order_manager.list_orders(page=0, results_per_page=10)
        if response.get("orders"):
            from rev_exporter.models import Order
            orders = [Order.from_api_response(o) for o in response["orders"]]
            completed = order_manager.filter_completed_orders(orders)
            assert isinstance(completed, list)
            if completed:
                assert all(o.is_completed() for o in completed)

