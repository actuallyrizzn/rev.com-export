"""
Order enumeration and retrieval functionality.
"""

import logging
from typing import List, Optional
from datetime import datetime

from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.models import Order, Attachment

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order enumeration and retrieval."""

    def __init__(self, client: RevAPIClient):
        """
        Initialize OrderManager.

        Args:
            client: RevAPIClient instance
        """
        self.client = client

    def list_orders(
        self, page: int = 0, results_per_page: int = 50
    ) -> Dict[str, any]:
        """
        List orders for a specific page.

        Args:
            page: Page number (0-indexed)
            results_per_page: Number of results per page

        Returns:
            Dictionary with:
                - total_count: Total number of orders
                - results_per_page: Results per page
                - page: Current page number
                - orders: List of order dictionaries
        """
        try:
            response = self.client.get(
                "/orders",
                params={"page": page, "results_per_page": results_per_page},
            )
            return response
        except RevAPIError as e:
            logger.error(f"Failed to list orders (page {page}): {e}")
            raise

    def get_all_orders(
        self, results_per_page: int = 50, since: Optional[datetime] = None
    ) -> List[Order]:
        """
        Get all orders with pagination.

        Args:
            results_per_page: Number of results per page
            since: Optional datetime to filter orders placed after this date

        Returns:
            List of Order objects
        """
        all_orders = []
        page = 0

        logger.info("Starting order enumeration...")

        while True:
            try:
                response = self.list_orders(page=page, results_per_page=results_per_page)
                orders_data = response.get("orders", [])

                if not orders_data:
                    # No more orders
                    break

                # Convert to Order objects
                for order_data in orders_data:
                    order = Order.from_api_response(order_data)

                    # Apply date filter if specified
                    if since and order.placed_on:
                        if order.placed_on < since:
                            # Orders are typically returned newest first,
                            # so if we hit an order older than 'since', we can stop
                            logger.info(
                                f"Reached order older than filter date, stopping pagination"
                            )
                            return all_orders

                    all_orders.append(order)

                logger.debug(
                    f"Retrieved page {page}: {len(orders_data)} orders "
                    f"(total so far: {len(all_orders)})"
                )

                # Check if we've retrieved all orders
                total_count = response.get("total_count", 0)
                if len(all_orders) >= total_count:
                    break

                page += 1

            except RevAPIError as e:
                logger.error(f"Error during pagination at page {page}: {e}")
                raise

        logger.info(f"Retrieved {len(all_orders)} total orders")
        return all_orders

    def get_order_details(self, order_number: str) -> Order:
        """
        Get detailed information for a specific order.

        Args:
            order_number: Order number

        Returns:
            Order object with full details including attachments
        """
        try:
            response = self.client.get(f"/orders/{order_number}")
            order = Order.from_api_response(response)
            logger.debug(f"Retrieved details for order {order_number}")
            return order
        except RevAPIError as e:
            logger.error(f"Failed to get order details for {order_number}: {e}")
            raise

    def filter_completed_orders(self, orders: List[Order]) -> List[Order]:
        """
        Filter orders to only include completed ones.

        Args:
            orders: List of Order objects

        Returns:
            List of completed Order objects
        """
        completed = [order for order in orders if order.is_completed()]
        logger.info(
            f"Filtered {len(completed)} completed orders from {len(orders)} total orders"
        )
        return completed

