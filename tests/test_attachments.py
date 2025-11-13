"""
Unit tests for attachments module.
"""

import pytest
from unittest.mock import Mock, patch

from rev_exporter.attachments import (
    AttachmentManager,
    AttachmentType,
)
from rev_exporter.client import RevAPIClient, RevAPIError
from rev_exporter.models import Attachment


class TestAttachmentManager:
    """Test AttachmentManager class."""

    def test_init(self, mock_api_client):
        """Test AttachmentManager initialization."""
        manager = AttachmentManager(mock_api_client)
        assert manager.client == mock_api_client

    def test_get_attachment_metadata(self, mock_api_client, sample_attachment_data):
        """Test getting attachment metadata."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = sample_attachment_data
            attachment = manager.get_attachment_metadata("att_001")

            assert isinstance(attachment, Attachment)
            assert attachment.id == "att_001"
            mock_get.assert_called_once_with("/attachments/att_001")

    def test_get_attachment_metadata_error(self, mock_api_client):
        """Test get_attachment_metadata with API error."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.side_effect = RevAPIError("Not found")

            with pytest.raises(RevAPIError):
                manager.get_attachment_metadata("att_001")

    def test_classify_transcript(self, mock_api_client):
        """Test classifying transcript attachment."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(
            id="att_001",
            name="transcript.json",
            type="transcript",
        )
        assert manager.classify_attachment(attachment) == AttachmentType.TRANSCRIPT

        attachment2 = Attachment(
            id="att_002",
            name="file.txt",
            type="transcription",
        )
        assert manager.classify_attachment(attachment2) == AttachmentType.TRANSCRIPT

    def test_classify_caption(self, mock_api_client):
        """Test classifying caption attachment."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(
            id="att_001",
            name="captions.srt",
            type="caption",
        )
        assert manager.classify_attachment(attachment) == AttachmentType.CAPTION

        attachment2 = Attachment(
            id="att_002",
            name="subtitles.vtt",
            type="subtitle",
        )
        assert manager.classify_attachment(attachment2) == AttachmentType.CAPTION

    def test_classify_media(self, mock_api_client):
        """Test classifying media attachment."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(
            id="att_001",
            name="audio.mp3",
            type="media",
        )
        assert manager.classify_attachment(attachment) == AttachmentType.MEDIA

        attachment2 = Attachment(
            id="att_002",
            name="video.mp4",
            type="video",
        )
        assert manager.classify_attachment(attachment2) == AttachmentType.MEDIA

    def test_classify_other(self, mock_api_client):
        """Test classifying unknown attachment type."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(
            id="att_001",
            name="unknown.file",
            type="unknown",
        )
        assert manager.classify_attachment(attachment) == AttachmentType.OTHER

    def test_download_attachment_content_with_format(self, mock_api_client):
        """Test downloading attachment with specific format."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = b"content"
            result = manager.download_attachment_content("att_001", format="json")

            assert result == b"content"
            mock_get.assert_called_once_with(
                "/attachments/att_001/content.json", stream=True
            )

    def test_download_attachment_content_preferred_formats(self, mock_api_client):
        """Test downloading with preferred formats."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            # First format fails, second succeeds
            mock_get.side_effect = [RevAPIError("Not found"), b"content"]
            result = manager.download_attachment_content(
                "att_001", preferred_formats=["json", "txt"]
            )

            assert result == b"content"
            assert mock_get.call_count == 2

    def test_download_attachment_content_default(self, mock_api_client):
        """Test downloading attachment with default format."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            mock_get.return_value = b"content"
            result = manager.download_attachment_content("att_001")

            assert result == b"content"
            mock_get.assert_called_once_with(
                "/attachments/att_001/content", stream=True
            )

    def test_get_preferred_format_transcript(self, mock_api_client):
        """Test getting preferred format for transcript."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="transcript", type="transcript")
        format = manager.get_preferred_format(AttachmentType.TRANSCRIPT, attachment)
        assert format == "json"

    def test_get_preferred_format_caption(self, mock_api_client):
        """Test getting preferred format for caption."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="caption", type="caption")
        format = manager.get_preferred_format(AttachmentType.CAPTION, attachment)
        assert format == "srt"

    def test_get_preferred_format_media(self, mock_api_client):
        """Test getting preferred format for media."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="audio", type="media")
        format = manager.get_preferred_format(AttachmentType.MEDIA, attachment)
        assert format is None

    def test_get_file_extension_from_format(self, mock_api_client):
        """Test getting file extension from format."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="file", type="transcript")
        ext = manager.get_file_extension(
            attachment, AttachmentType.TRANSCRIPT, "json"
        )
        assert ext == ".json"

    def test_get_file_extension_from_name(self, mock_api_client):
        """Test getting file extension from attachment name."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="file.mp3", type="media")
        ext = manager.get_file_extension(attachment, AttachmentType.MEDIA, None)
        assert ext == ".mp3"

    def test_get_file_extension_default(self, mock_api_client):
        """Test getting default file extension."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="file", type="transcript")
        ext = manager.get_file_extension(attachment, AttachmentType.TRANSCRIPT, None)
        assert ext == ".txt"

        attachment2 = Attachment(id="att_002", name="file", type="caption")
        ext2 = manager.get_file_extension(attachment2, AttachmentType.CAPTION, None)
        assert ext2 == ".srt"

        attachment3 = Attachment(id="att_003", name="file", type="media")
        ext3 = manager.get_file_extension(attachment3, AttachmentType.MEDIA, None)
        assert ext3 == ".mp3"

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test invalid characters
        assert AttachmentManager.sanitize_filename("file<>name") == "file__name"
        assert AttachmentManager.sanitize_filename("file:name") == "file_name"
        assert AttachmentManager.sanitize_filename("file/name") == "file_name"

        # Test leading/trailing spaces
        assert AttachmentManager.sanitize_filename("  filename  ") == "filename"
        assert AttachmentManager.sanitize_filename("...filename...") == "filename"

        # Test length limit
        long_name = "a" * 300
        sanitized = AttachmentManager.sanitize_filename(long_name)
        assert len(sanitized) == 200

        # Test normal filename
        assert AttachmentManager.sanitize_filename("normal_file.txt") == "normal_file.txt"

    def test_download_attachment_content_format_fallback(self, mock_api_client):
        """Test download with format fallback."""
        manager = AttachmentManager(mock_api_client)

        with patch.object(mock_api_client, "get") as mock_get:
            # First call fails, second succeeds
            mock_get.side_effect = [RevAPIError("Not found"), b"content"]
            result = manager.download_attachment_content("att_001", format="json")

            assert result == b"content"
            assert mock_get.call_count == 2

    def test_get_file_extension_fallback(self, mock_api_client):
        """Test file extension fallback for unknown types."""
        manager = AttachmentManager(mock_api_client)

        attachment = Attachment(id="att_001", name="file", type="unknown")
        ext = manager.get_file_extension(attachment, AttachmentType.OTHER, None)
        assert ext == ".bin"

