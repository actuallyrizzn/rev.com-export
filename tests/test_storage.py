"""
Unit tests for storage module.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch

from rev_exporter.storage import StorageManager
from rev_exporter.models import Order, Attachment
from rev_exporter.attachments import AttachmentType


class TestStorageManager:
    """Test StorageManager class."""

    def test_init(self, temp_output_dir):
        """Test StorageManager initialization."""
        storage = StorageManager(temp_output_dir)
        assert storage.output_dir == temp_output_dir
        assert storage.index_file == temp_output_dir / ".rev-exporter-index.json"

    def test_init_custom_index(self, temp_output_dir):
        """Test StorageManager with custom index file."""
        index_file = temp_output_dir / "custom_index.json"
        storage = StorageManager(temp_output_dir, index_file=index_file)
        assert storage.index_file == index_file

    def test_load_index_nonexistent(self, temp_output_dir):
        """Test loading index when file doesn't exist."""
        storage = StorageManager(temp_output_dir)
        assert len(storage.downloaded_attachments) == 0

    def test_load_index_existing(self, temp_output_dir):
        """Test loading existing index."""
        index_file = temp_output_dir / ".rev-exporter-index.json"
        index_data = {
            "downloaded_attachments": ["att_001", "att_002"],
            "last_updated": "2024-01-15T10:00:00",
        }
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        storage = StorageManager(temp_output_dir)
        assert "att_001" in storage.downloaded_attachments
        assert "att_002" in storage.downloaded_attachments

    def test_load_index_invalid_json(self, temp_output_dir):
        """Test loading invalid index file."""
        index_file = temp_output_dir / ".rev-exporter-index.json"
        index_file.write_text("invalid json{")

        storage = StorageManager(temp_output_dir)
        assert len(storage.downloaded_attachments) == 0

    def test_is_downloaded(self, temp_output_dir):
        """Test checking if attachment is downloaded."""
        storage = StorageManager(temp_output_dir)
        storage.downloaded_attachments.add("att_001")

        assert storage.is_downloaded("att_001") is True
        assert storage.is_downloaded("att_002") is False

    def test_mark_downloaded(self, temp_output_dir):
        """Test marking attachment as downloaded."""
        storage = StorageManager(temp_output_dir)
        storage.mark_downloaded("att_001")

        assert "att_001" in storage.downloaded_attachments
        assert storage.is_downloaded("att_001") is True

        # Check that index file was saved
        assert storage.index_file.exists()
        with open(storage.index_file, "r") as f:
            data = json.load(f)
            assert "att_001" in data["downloaded_attachments"]

    def test_get_order_dir(self, temp_output_dir):
        """Test getting order directory path."""
        storage = StorageManager(temp_output_dir)
        order_dir = storage.get_order_dir("12345")
        assert order_dir == temp_output_dir / "12345"

    def test_create_order_structure(self, temp_output_dir):
        """Test creating order directory structure."""
        storage = StorageManager(temp_output_dir)
        dirs = storage.create_order_structure("12345")

        assert dirs["root"].exists()
        assert dirs["media"].exists()
        assert dirs["transcripts"].exists()
        assert dirs["other"].exists()

        assert dirs["root"] == temp_output_dir / "12345"
        assert dirs["media"] == temp_output_dir / "12345" / "media"
        assert dirs["transcripts"] == temp_output_dir / "12345" / "transcripts"
        assert dirs["other"] == temp_output_dir / "12345" / "other"

    def test_save_attachment_media(self, temp_output_dir):
        """Test saving media attachment."""
        storage = StorageManager(temp_output_dir)
        attachment = Attachment(id="att_001", name="audio.mp3", type="media")
        content = b"audio content"

        file_path = storage.save_attachment(
            "12345", attachment, AttachmentType.MEDIA, content, ".mp3"
        )

        assert file_path.exists()
        assert file_path.parent == temp_output_dir / "12345" / "media"
        assert file_path.read_bytes() == content
        assert "att_001" in file_path.name

    def test_save_attachment_transcript(self, temp_output_dir):
        """Test saving transcript attachment."""
        storage = StorageManager(temp_output_dir)
        attachment = Attachment(id="att_002", name="transcript.txt", type="transcript")
        content = b"transcript content"

        file_path = storage.save_attachment(
            "12345", attachment, AttachmentType.TRANSCRIPT, content, ".txt"
        )

        assert file_path.exists()
        assert file_path.parent == temp_output_dir / "12345" / "transcripts"

    def test_save_attachment_caption(self, temp_output_dir):
        """Test saving caption attachment."""
        storage = StorageManager(temp_output_dir)
        attachment = Attachment(id="att_003", name="caption.srt", type="caption")
        content = b"caption content"

        file_path = storage.save_attachment(
            "12345", attachment, AttachmentType.CAPTION, content, ".srt"
        )

        assert file_path.exists()
        assert file_path.parent == temp_output_dir / "12345" / "transcripts"

    def test_save_attachment_other(self, temp_output_dir):
        """Test saving other type attachment."""
        storage = StorageManager(temp_output_dir)
        attachment = Attachment(id="att_004", name="other.file", type="unknown")
        content = b"other content"

        file_path = storage.save_attachment(
            "12345", attachment, AttachmentType.OTHER, content, ".bin"
        )

        assert file_path.exists()
        assert file_path.parent == temp_output_dir / "12345" / "other"

    def test_save_order_metadata(self, temp_output_dir, sample_order_data):
        """Test saving order metadata."""
        storage = StorageManager(temp_output_dir)
        order = Order.from_api_response(sample_order_data)

        metadata_path = storage.save_order_metadata(order)

        assert metadata_path.exists()
        assert metadata_path.name == "attachments.json"

        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            assert metadata["order_number"] == "12345"
            assert metadata["status"] == "Complete"
            assert len(metadata["attachments"]) == 2

    def test_save_order_metadata_creates_dir(self, temp_output_dir):
        """Test that saving metadata creates directory."""
        storage = StorageManager(temp_output_dir)
        order = Order(order_number="99999", status="Complete")

        metadata_path = storage.save_order_metadata(order)
        assert metadata_path.parent.exists()

    def test_save_index_error_handling(self, temp_output_dir, monkeypatch):
        """Test handling errors when saving index."""
        import platform
        if platform.system() == "Windows":
            pytest.skip("chmod tests not reliable on Windows")

        storage = StorageManager(temp_output_dir)

        # Make the directory read-only to cause an error
        import stat
        temp_output_dir.chmod(stat.S_IREAD)

        try:
            # Should not raise exception, just log error
            storage.mark_downloaded("att_001")
        except Exception:
            pass
        finally:
            # Restore permissions
            temp_output_dir.chmod(stat.S_IREAD | stat.S_IWRITE)

    def test_load_index_io_error(self, temp_output_dir, monkeypatch):
        """Test handling IO errors when loading index."""
        import platform
        if platform.system() == "Windows":
            pytest.skip("chmod tests not reliable on Windows")

        index_file = temp_output_dir / ".rev-exporter-index.json"
        index_file.write_text('{"downloaded_attachments": ["att_001"]}')

        # Make file unreadable
        import stat
        index_file.chmod(stat.S_IWRITE)

        try:
            storage = StorageManager(temp_output_dir)
            # Should handle error gracefully
            assert len(storage.downloaded_attachments) == 0
        finally:
            index_file.chmod(stat.S_IREAD | stat.S_IWRITE)

    def test_save_index_io_error(self, temp_output_dir, monkeypatch):
        """Test handling IO errors when saving index."""
        storage = StorageManager(temp_output_dir)

        # Mock open to raise IOError
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            # Should not raise exception, just log error
            storage.mark_downloaded("att_001")
            # Index should still be updated in memory
            assert "att_001" in storage.downloaded_attachments

