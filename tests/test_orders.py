"""
Unit tests for orders module.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from rev_exporter.orders import OrderManager
from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.models import Order


class TestOrderManager:
    """Test OrderManager class."""

    def test_init(self, mock_api_client):
        """Test OrderManager initialization."""
        manager = OrderManager(mock_api_client)
        assert manager.client == mock_api_client

    def test_list_orders(self, mock_api_client, sample_orders_list_response):
        """Test listing orders."""
        manager = OrderManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = sample_orders_list_response
            result = manager.list_orders(page=0, results_per_page=50)

            assert result["total_count"] == 2
            assert len(result["orders"]) == 2
            mock_get.assert_called_once_with(
                "/orders", params={"page": 0, "results_per_page": 50}
            )

    def test_list_orders_with_params(self, mock_api_client):
        """Test listing orders with custom parameters."""
        manager = OrderManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = {"orders": []}
            manager.list_orders(page=2, results_per_page=25)

            mock_get.assert_called_once_with(
                "/orders", params={"page": 2, "results_per_page": 25}
            )

    def test_list_orders_error(self, mock_api_client):
        """Test list_orders with API error."""
        manager = OrderManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.side_effect = RevAPIError("API error")

            with pytest.raises(RevAPIError):
                manager.list_orders()

    def test_get_all_orders_single_page(self, mock_api_client):
        """Test getting all orders from single page."""
        manager = OrderManager(mock_api_client)

        response = {
            "total_count": 2,
            "results_per_page": 50,
            "page": 0,
            "orders": [
                {"order_number": "1", "status": "Complete", "placed_on": "2024-01-15T10:00:00Z"},
                {"order_number": "2", "status": "Complete", "placed_on": "2024-01-16T10:00:00Z"},
            ],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = response
            orders = manager.get_all_orders()

            assert len(orders) == 2
            assert all(isinstance(o, Order) for o in orders)

    def test_get_all_orders_multiple_pages(self, mock_api_client):
        """Test getting all orders across multiple pages."""
        manager = OrderManager(mock_api_client)

        page1 = {
            "total_count": 3,
            "results_per_page": 2,
            "page": 0,
            "orders": [
                {"order_number": "1", "status": "Complete", "placed_on": "2024-01-15T10:00:00Z"},
                {"order_number": "2", "status": "Complete", "placed_on": "2024-01-16T10:00:00Z"},
            ],
        }

        page2 = {
            "total_count": 3,
            "results_per_page": 2,
            "page": 1,
            "orders": [
                {"order_number": "3", "status": "Complete", "placed_on": "2024-01-17T10:00:00Z"},
            ],
        }

        page3 = {
            "total_count": 3,
            "results_per_page": 2,
            "page": 2,
            "orders": [],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.side_effect = [page1, page2, page3]
            orders = manager.get_all_orders(results_per_page=2)

            assert len(orders) == 3
            # Should stop when total_count is reached, so might be 2 calls
            assert mock_get.call_count >= 2

    def test_get_all_orders_empty(self, mock_api_client):
        """Test getting all orders when none exist."""
        manager = OrderManager(mock_api_client)

        response = {
            "total_count": 0,
            "results_per_page": 50,
            "page": 0,
            "orders": [],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = response
            orders = manager.get_all_orders()

            assert len(orders) == 0

    def test_get_all_orders_with_since_filter(self, mock_api_client):
        """Test getting orders with date filter."""
        from datetime import timezone
        manager = OrderManager(mock_api_client)

        since_date = datetime(2024, 1, 16, tzinfo=timezone.utc)

        # Orders are returned newest first, so order 2 (newer) comes first
        response = {
            "total_count": 2,
            "results_per_page": 50,
            "page": 0,
            "orders": [
                {"order_number": "2", "status": "Complete", "placed_on": "2024-01-17T10:00:00Z"},
                {"order_number": "1", "status": "Complete", "placed_on": "2024-01-15T10:00:00Z"},
            ],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = response
            orders = manager.get_all_orders(since=since_date)

            # Should include order 2 (after since_date) and stop when it hits order 1 (before)
            assert len(orders) == 1
            assert orders[0].order_number == "2"

    def test_get_order_details(self, mock_api_client, sample_order_data):
        """Test getting order details."""
        manager = OrderManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = sample_order_data
            order = manager.get_order_details("12345")

            assert isinstance(order, Order)
            assert order.order_number == "12345"
            assert len(order.attachments) == 2
            mock_get.assert_called_once_with("/orders/12345")

    def test_get_order_details_error(self, mock_api_client):
        """Test get_order_details with API error."""
        manager = OrderManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.side_effect = RevAPIError("Not found")

            with pytest.raises(RevAPIError):
                manager.get_order_details("12345")

    def test_filter_completed_orders(self, mock_api_client):
        """Test filtering completed orders."""
        manager = OrderManager(mock_api_client)

        orders = [
            Order(order_number="1", status="Complete"),
            Order(order_number="2", status="In Progress"),
            Order(order_number="3", status="Complete"),
            Order(order_number="4", status="Pending"),
        ]

        completed = manager.filter_completed_orders(orders)
        assert len(completed) == 2
        assert all(o.status.lower() == "complete" for o in completed)

    def test_filter_completed_orders_empty(self, mock_api_client):
        """Test filtering when no completed orders."""
        manager = OrderManager(mock_api_client)

        orders = [
            Order(order_number="1", status="Pending"),
            Order(order_number="2", status="In Progress"),
        ]

        completed = manager.filter_completed_orders(orders)
        assert len(completed) == 0

    def test_get_all_orders_stops_at_total_count(self, mock_api_client):
        """Test that pagination stops when total_count is reached."""
        manager = OrderManager(mock_api_client)

        page1 = {
            "total_count": 2,
            "results_per_page": 1,
            "page": 0,
            "orders": [
                {"order_number": "1", "status": "Complete", "placed_on": "2024-01-15T10:00:00Z"},
            ],
        }

        page2 = {
            "total_count": 2,
            "results_per_page": 1,
            "page": 1,
            "orders": [
                {"order_number": "2", "status": "Complete", "placed_on": "2024-01-16T10:00:00Z"},
            ],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.side_effect = [page1, page2]
            orders = manager.get_all_orders(results_per_page=1)

            assert len(orders) == 2
            assert mock_get.call_count == 2

    def test_get_all_orders_with_since_stops_early(self, mock_api_client):
        """Test that date filtering stops pagination early."""
        from datetime import timezone
        manager = OrderManager(mock_api_client)

        since_date = datetime(2024, 1, 16, tzinfo=timezone.utc)

        # First page has orders before and after since_date
        page1 = {
            "total_count": 3,
            "results_per_page": 1,
            "page": 0,
            "orders": [
                {"order_number": "1", "status": "Complete", "placed_on": "2024-01-15T10:00:00Z"},
            ],
        }

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = page1
            orders = manager.get_all_orders(since=since_date, results_per_page=1)

            # Should stop early when order is older than since_date
            assert len(orders) == 0  # Order is older, so should be filtered out and stop

