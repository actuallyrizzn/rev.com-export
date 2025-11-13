"""
Attachment processing and download functionality.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum

from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.models import Attachment

logger = logging.getLogger(__name__)


class AttachmentType(Enum):
    """Attachment type categories."""

    MEDIA = "media"
    TRANSCRIPT = "transcript"
    CAPTION = "caption"
    OTHER = "other"


class AttachmentManager:
    """Manages attachment metadata retrieval, classification, and downloads."""

    def __init__(self, client: RevAPIClient):
        """
        Initialize AttachmentManager.

        Args:
            client: RevAPIClient instance
        """
        self.client = client

    def get_attachment_metadata(self, attachment_id: str) -> Attachment:
        """
        Get detailed metadata for an attachment.

        Args:
            attachment_id: Attachment ID

        Returns:
            Attachment object with full metadata
        """
        try:
            response = self.client.get(f"/attachments/{attachment_id}")
            attachment = Attachment.from_api_response(response)
            logger.debug(f"Retrieved metadata for attachment {attachment_id}")
            return attachment
        except RevAPIError as e:
            logger.error(f"Failed to get attachment metadata for {attachment_id}: {e}")
            raise

    def classify_attachment(self, attachment: Attachment) -> AttachmentType:
        """
        Classify attachment type based on documented fields.

        Uses only 'type' and 'name' fields as per PRD requirements.

        Args:
            attachment: Attachment object

        Returns:
            AttachmentType enum value
        """
        # Check type field first
        att_type = attachment.type.lower() if attachment.type else ""
        name = attachment.name.lower() if attachment.name else ""

        # Transcript indicators
        transcript_keywords = ["transcript", "transcription", "txt", "json", "docx"]
        if any(keyword in att_type or keyword in name for keyword in transcript_keywords):
            return AttachmentType.TRANSCRIPT

        # Caption indicators
        caption_keywords = ["caption", "srt", "vtt", "subtitle"]
        if any(keyword in att_type or keyword in name for keyword in caption_keywords):
            return AttachmentType.CAPTION

        # Media indicators
        media_keywords = ["media", "audio", "video", "mp3", "mp4", "wav", "m4a", "mov", "avi"]
        if any(keyword in att_type or keyword in name for keyword in media_keywords):
            return AttachmentType.MEDIA

        # Default to other
        return AttachmentType.OTHER

    def download_attachment_content(
        self,
        attachment_id: str,
        format: Optional[str] = None,
        preferred_formats: Optional[List[str]] = None,
    ) -> bytes:
        """
        Download attachment content.

        Args:
            attachment_id: Attachment ID
            format: Specific format extension (e.g., 'json', 'txt', 'srt')
            preferred_formats: List of preferred formats to try in order

        Returns:
            Binary content of the attachment
        """
        # If specific format requested, use it
        if format:
            endpoint = f"/attachments/{attachment_id}/content.{format}"
            try:
                return self.client.get(endpoint, stream=True)  # type: ignore
            except RevAPIError:
                # Fallback to default if format not available
                logger.warning(
                    f"Format {format} not available for {attachment_id}, trying default"
                )

        # Try preferred formats if provided
        if preferred_formats:
            for fmt in preferred_formats:
                endpoint = f"/attachments/{attachment_id}/content.{fmt}"
                try:
                    return self.client.get(endpoint, stream=True)  # type: ignore
                except RevAPIError:
                    continue

        # Default: try without extension
        endpoint = f"/attachments/{attachment_id}/content"
        return self.client.get(endpoint, stream=True)  # type: ignore

    def get_preferred_format(
        self, attachment_type: AttachmentType, attachment: Attachment
    ) -> Optional[str]:
        """
        Get preferred format for an attachment based on its type.

        Args:
            attachment_type: Classified attachment type
            attachment: Attachment object

        Returns:
            Preferred format extension or None
        """
        if attachment_type == AttachmentType.TRANSCRIPT:
            # Prefer JSON or TXT for transcripts
            # Check if JSON is available by trying it
            return "json"  # Default preference, will fallback if not available

        if attachment_type == AttachmentType.CAPTION:
            # Prefer SRT for captions
            return "srt"

        # For media and other, use server default (no format specified)
        return None

    def get_file_extension(
        self, attachment: Attachment, attachment_type: AttachmentType, format: Optional[str]
    ) -> str:
        """
        Determine file extension for saved file.

        Args:
            attachment: Attachment object
            attachment_type: Classified attachment type
            format: Format used for download

        Returns:
            File extension (with leading dot)
        """
        # If format was specified, use it
        if format:
            return f".{format}"

        # Try to extract from name
        if attachment.name:
            match = re.search(r"\.([a-z0-9]+)$", attachment.name, re.IGNORECASE)
            if match:
                return f".{match.group(1).lower()}"

        # Default based on type
        if attachment_type == AttachmentType.TRANSCRIPT:
            return ".txt"
        if attachment_type == AttachmentType.CAPTION:
            return ".srt"
        if attachment_type == AttachmentType.MEDIA:
            return ".mp3"  # Default for media

        return ".bin"  # Fallback

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for filesystem safety.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(" .")
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename

