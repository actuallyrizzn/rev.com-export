"""
Data models for Rev Exporter.

Defines Order and Attachment data structures.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Attachment:
    """Represents an attachment from Rev.com."""

    id: str
    name: str
    type: str
    download_uri: Optional[str] = None
    # Additional fields that may be present
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Attachment":
        """
        Create Attachment from API response.

        Args:
            data: Dictionary from API response

        Returns:
            Attachment instance
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            download_uri=data.get("download_uri"),
            metadata=data,
        )


@dataclass
class Order:
    """Represents an order from Rev.com."""

    order_number: str
    status: str
    placed_on: Optional[datetime] = None
    attachments: List[Attachment] = None
    # Additional fields that may be present
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.attachments is None:
            self.attachments = []

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "Order":
        """
        Create Order from API response.

        Args:
            data: Dictionary from API response

        Returns:
            Order instance
        """
        # Parse placed_on if present
        placed_on = None
        if "placed_on" in data:
            try:
                # Try parsing ISO format datetime
                placed_on_str = data["placed_on"]
                if isinstance(placed_on_str, str):
                    placed_on = datetime.fromisoformat(placed_on_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        # Parse attachments if present
        attachments = []
        if "attachments" in data and isinstance(data["attachments"], list):
            attachments = [
                Attachment.from_api_response(att) for att in data["attachments"]
            ]

        return cls(
            order_number=data.get("order_number", ""),
            status=data.get("status", ""),
            placed_on=placed_on,
            attachments=attachments,
            metadata=data,
        )

    def is_completed(self) -> bool:
        """
        Check if order is completed.

        Based on Rev API documentation, completed orders typically have
        status "Complete" or "Completed". This may need adjustment based
        on actual API responses.

        Returns:
            True if order is completed
        """
        # Common completed status values (may need to verify with actual API)
        completed_statuses = ["complete", "completed", "done", "finished"]
        return self.status.lower() in completed_statuses

