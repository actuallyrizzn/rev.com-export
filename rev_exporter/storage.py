"""
File storage and idempotency management.
"""

import json
import logging
from pathlib import Path
from typing import Set, Dict, Any, Optional
from datetime import datetime

from rev_exporter.models import Order, Attachment
from rev_exporter.attachments import AttachmentType, AttachmentManager

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages file storage and idempotency."""

    def __init__(self, output_dir: Path, index_file: Optional[Path] = None):
        """
        Initialize StorageManager.

        Args:
            output_dir: Root directory for exports
            index_file: Path to index file for tracking downloads
        """
        self.output_dir = Path(output_dir)
        self.index_file = index_file or self.output_dir / ".rev-exporter-index.json"
        self.downloaded_attachments: Set[str] = set()
        self._load_index()

    def _load_index(self) -> None:
        """Load the download index from file."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    data = json.load(f)
                    self.downloaded_attachments = set(data.get("downloaded_attachments", []))
                logger.debug(
                    f"Loaded index with {len(self.downloaded_attachments)} downloaded attachments"
                )
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load index file: {e}")

    def _save_index(self) -> None:
        """Save the download index to file."""
        try:
            data = {
                "downloaded_attachments": list(self.downloaded_attachments),
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.index_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save index file: {e}")

    def is_downloaded(self, attachment_id: str) -> bool:
        """
        Check if an attachment has already been downloaded.

        Args:
            attachment_id: Attachment ID

        Returns:
            True if already downloaded
        """
        return attachment_id in self.downloaded_attachments

    def mark_downloaded(self, attachment_id: str) -> None:
        """
        Mark an attachment as downloaded.

        Args:
            attachment_id: Attachment ID
        """
        self.downloaded_attachments.add(attachment_id)
        self._save_index()

    def get_order_dir(self, order_number: str) -> Path:
        """
        Get the directory path for an order.

        Args:
            order_number: Order number

        Returns:
            Path to order directory
        """
        return self.output_dir / order_number

    def create_order_structure(self, order_number: str) -> Dict[str, Path]:
        """
        Create directory structure for an order.

        Args:
            order_number: Order number

        Returns:
            Dictionary with paths: media, transcripts, other
        """
        order_dir = self.get_order_dir(order_number)
        order_dir.mkdir(parents=True, exist_ok=True)

        media_dir = order_dir / "media"
        transcripts_dir = order_dir / "transcripts"
        other_dir = order_dir / "other"

        media_dir.mkdir(exist_ok=True)
        transcripts_dir.mkdir(exist_ok=True)
        other_dir.mkdir(exist_ok=True)

        return {
            "root": order_dir,
            "media": media_dir,
            "transcripts": transcripts_dir,
            "other": other_dir,
        }

    def save_attachment(
        self,
        order_number: str,
        attachment: Attachment,
        attachment_type: AttachmentType,
        content: bytes,
        file_extension: str,
    ) -> Path:
        """
        Save an attachment to disk.

        Args:
            order_number: Order number
            attachment: Attachment object
            attachment_type: Classified attachment type
            content: Binary content
            file_extension: File extension (with leading dot)

        Returns:
            Path to saved file
        """
        # Create directory structure
        dirs = self.create_order_structure(order_number)

        # Determine target directory
        if attachment_type == AttachmentType.MEDIA:
            target_dir = dirs["media"]
        elif attachment_type == AttachmentType.TRANSCRIPT:
            target_dir = dirs["transcripts"]
        elif attachment_type == AttachmentType.CAPTION:
            target_dir = dirs["transcripts"]  # Captions go with transcripts
        else:
            target_dir = dirs["other"]

        # Generate filename: <attachment_id>_<sanitized_name>.<ext>
        from rev_exporter.attachments import AttachmentManager

        sanitized_name = AttachmentManager.sanitize_filename(attachment.name or "attachment")
        filename = f"{attachment.id}_{sanitized_name}{file_extension}"

        file_path = target_dir / filename

        # Write file
        with open(file_path, "wb") as f:
            f.write(content)

        logger.debug(f"Saved attachment {attachment.id} to {file_path}")
        return file_path

    def save_order_metadata(self, order: Order) -> Path:
        """
        Save order metadata as JSON.

        Args:
            order: Order object

        Returns:
            Path to saved metadata file
        """
        order_dir = self.get_order_dir(order.order_number)
        order_dir.mkdir(parents=True, exist_ok=True)

        metadata_file = order_dir / "attachments.json"

        # Prepare metadata (exclude binary data if any)
        metadata = {
            "order_number": order.order_number,
            "status": order.status,
            "placed_on": order.placed_on.isoformat() if order.placed_on else None,
            "attachments": [
                {
                    "id": att.id,
                    "name": att.name,
                    "type": att.type,
                    "download_uri": att.download_uri,
                }
                for att in order.attachments
            ],
        }

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.debug(f"Saved order metadata to {metadata_file}")
        return metadata_file

