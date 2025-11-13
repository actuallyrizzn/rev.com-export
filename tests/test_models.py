"""
Unit tests for models module.
"""

import pytest
from datetime import datetime

from rev_exporter.models import Order, Attachment


class TestAttachment:
    """Test Attachment model."""

    def test_from_api_response(self, sample_attachment_data):
        """Test creating Attachment from API response."""
        attachment = Attachment.from_api_response(sample_attachment_data)
        assert attachment.id == "att_001"
        assert attachment.name == "transcript.json"
        assert attachment.type == "transcript"
        assert attachment.download_uri == "https://example.com/download/att_001"

    def test_from_api_response_minimal(self):
        """Test creating Attachment with minimal data."""
        data = {"id": "att_002", "name": "file.txt"}
        attachment = Attachment.from_api_response(data)
        assert attachment.id == "att_002"
        assert attachment.name == "file.txt"
        assert attachment.type == ""

    def test_metadata_stored(self, sample_attachment_data):
        """Test that full metadata is stored."""
        attachment = Attachment.from_api_response(sample_attachment_data)
        assert attachment.metadata == sample_attachment_data


class TestOrder:
    """Test Order model."""

    def test_from_api_response(self, sample_order_data):
        """Test creating Order from API response."""
        order = Order.from_api_response(sample_order_data)
        assert order.order_number == "12345"
        assert order.status == "Complete"
        assert isinstance(order.placed_on, datetime)
        assert len(order.attachments) == 2

    def test_from_api_response_minimal(self):
        """Test creating Order with minimal data."""
        data = {"order_number": "123", "status": "Pending"}
        order = Order.from_api_response(data)
        assert order.order_number == "123"
        assert order.status == "Pending"
        assert order.placed_on is None
        assert len(order.attachments) == 0

    def test_is_completed(self):
        """Test is_completed method."""
        complete_order = Order(order_number="1", status="Complete")
        assert complete_order.is_completed() is True

        completed_order = Order(order_number="2", status="Completed")
        assert completed_order.is_completed() is True

        in_progress_order = Order(order_number="3", status="In Progress")
        assert in_progress_order.is_completed() is False

        pending_order = Order(order_number="4", status="Pending")
        assert pending_order.is_completed() is False

    def test_is_completed_case_insensitive(self):
        """Test is_completed is case insensitive."""
        order1 = Order(order_number="1", status="COMPLETE")
        assert order1.is_completed() is True

        order2 = Order(order_number="2", status="complete")
        assert order2.is_completed() is True

    def test_attachments_default_empty(self):
        """Test that attachments default to empty list."""
        order = Order(order_number="1", status="Pending")
        assert order.attachments == []

    def test_placed_on_parsing(self):
        """Test parsing placed_on datetime."""
        data = {
            "order_number": "1",
            "status": "Complete",
            "placed_on": "2024-01-15T10:30:00Z",
        }
        order = Order.from_api_response(data)
        assert isinstance(order.placed_on, datetime)
        assert order.placed_on.year == 2024
        assert order.placed_on.month == 1
        assert order.placed_on.day == 15

    def test_placed_on_invalid_format(self):
        """Test handling invalid placed_on format."""
        data = {
            "order_number": "1",
            "status": "Complete",
            "placed_on": "invalid-date",
        }
        order = Order.from_api_response(data)
        assert order.placed_on is None

    def test_metadata_stored(self, sample_order_data):
        """Test that full metadata is stored."""
        order = Order.from_api_response(sample_order_data)
        assert order.metadata == sample_order_data

