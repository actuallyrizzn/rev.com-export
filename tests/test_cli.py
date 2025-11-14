"""
Unit tests for CLI module.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from rev_exporter.cli import main
from rev_exporter.config import Config
from rev_exporter.attachments import AttachmentType


class TestCLI:
    """Test CLI commands."""

    def test_main_group(self):
        """Test main CLI group."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Rev Exporter" in result.output

    def test_test_connection_success(self, monkeypatch):
        """Test test-connection command success."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.RevAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.test_connection.return_value = True
            mock_client_class.return_value = mock_client

            result = runner.invoke(main, ["test-connection"])
            assert result.exit_code == 0
            assert "successful" in result.output.lower()

    def test_test_connection_failure(self, monkeypatch):
        """Test test-connection command failure."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.RevAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.test_connection.return_value = False
            mock_client_class.return_value = mock_client

            result = runner.invoke(main, ["test-connection"])
            assert result.exit_code == 1
            assert "failed" in result.output.lower()

    def test_test_connection_unconfigured(self, monkeypatch, tmp_path):
        """Test test-connection when not configured."""
        # Clear environment
        monkeypatch.delenv("REV_CLIENT_API_KEY", raising=False)
        monkeypatch.delenv("REV_USER_API_KEY", raising=False)
        monkeypatch.delenv("REV_API_KEY", raising=False)
        # Mock Path.cwd to prevent loading from docs/key.md
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["test-connection"])
        assert result.exit_code == 1
        assert "not configured" in result.output.lower()

    def test_sync_basic(self, monkeypatch, tmp_path):
        """Test sync command basic functionality."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            # Setup mocks
            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = []
            mock_order_mgr.filter_completed_orders.return_value = []
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            assert "No completed orders" in result.output or "0" in result.output

    def test_sync_dry_run(self, monkeypatch, tmp_path):
        """Test sync command with dry-run."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        order.attachments = [
            Attachment(id="att_001", name="test.txt", type="transcript"),
        ]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.return_value = AttachmentType.TRANSCRIPT
            mock_att_mgr.get_preferred_format.return_value = "txt"
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports"), "--dry-run"],
            )

            assert result.exit_code == 0
            assert "DRY RUN" in result.output
            # Storage should not be called in dry-run
            mock_storage.save_attachment.assert_not_called()

    def test_sync_with_flags(self, monkeypatch, tmp_path):
        """Test sync command with various flags."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager"), \
             patch("rev_exporter.cli.StorageManager"):

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = []
            mock_order_mgr.filter_completed_orders.return_value = []
            mock_order_mgr_class.return_value = mock_order_mgr

            # Test without --since first (it's optional)
            # Note: --debug is a global option, must come before the command
            result = runner.invoke(
                main,
                [
                    "--debug",
                    "sync",
                    "--output-dir", str(tmp_path / "exports"),
                    "--no-include-media",
                ],
            )

            assert result.exit_code == 0

    def test_sync_keyboard_interrupt(self, monkeypatch, tmp_path):
        """Test sync command handling keyboard interrupt."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class:
            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.side_effect = KeyboardInterrupt()
            mock_order_mgr_class.return_value = mock_order_mgr

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 1
            assert "Interrupted" in result.output

    def test_sync_exception_handling(self, monkeypatch, tmp_path):
        """Test sync command exception handling."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class:
            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.side_effect = Exception("Unexpected error")
            mock_order_mgr_class.return_value = mock_order_mgr

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 1
            assert "Fatal error" in result.output

    def test_main_debug_flag(self):
        """Test main command with debug flag."""
        runner = CliRunner()
        result = runner.invoke(main, ["--debug", "test-connection", "--help"])
        # Should not error, just show help
        assert result.exit_code in [0, 1]  # Help might exit with 1

    def test_test_connection_exception(self, monkeypatch):
        """Test test-connection with exception."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        with patch("rev_exporter.cli.RevAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.test_connection.side_effect = Exception("Unexpected error")
            mock_client_class.return_value = mock_client

            result = runner.invoke(main, ["test-connection"])
            assert result.exit_code == 1
            assert "[ERROR]" in result.output

    def test_sync_not_configured(self, monkeypatch, tmp_path):
        """Test sync when not configured."""
        monkeypatch.delenv("REV_CLIENT_API_KEY", raising=False)
        monkeypatch.delenv("REV_USER_API_KEY", raising=False)
        monkeypatch.delenv("REV_API_KEY", raising=False)
        # Mock Path.cwd to prevent loading from docs/key.md
        monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

        runner = CliRunner()
        result = runner.invoke(main, ["sync", "--output-dir", str(tmp_path / "exports")])
        assert result.exit_code == 1
        assert "not configured" in result.output

    def test_sync_with_actual_downloads(self, monkeypatch, tmp_path):
        """Test sync command with actual file downloads."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        attachment1 = Attachment(id="att_001", name="transcript.txt", type="transcript")
        attachment2 = Attachment(id="att_002", name="audio.mp3", type="media")
        order.attachments = [attachment1, attachment2]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.side_effect = [
                AttachmentType.TRANSCRIPT,
                AttachmentType.MEDIA,
            ]
            mock_att_mgr.get_preferred_format.return_value = "txt"
            mock_att_mgr.get_attachment_metadata.return_value = attachment1
            mock_att_mgr.download_attachment_content.return_value = b"content"
            mock_att_mgr.get_file_extension.return_value = ".txt"
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage.save_attachment.return_value = tmp_path / "file.txt"
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            # Verify storage methods were called
            assert mock_storage.save_order_metadata.called
            assert mock_storage.save_attachment.called
            assert mock_storage.mark_downloaded.called

    def test_sync_with_skipped_attachment(self, monkeypatch, tmp_path):
        """Test sync with already downloaded attachment."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        attachment = Attachment(id="att_001", name="transcript.txt", type="transcript")
        order.attachments = [attachment]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = True  # Already downloaded
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            # Should skip download
            mock_storage.save_attachment.assert_not_called()

    def test_sync_with_attachment_error(self, monkeypatch, tmp_path):
        """Test sync with attachment download error."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        attachment = Attachment(id="att_001", name="transcript.txt", type="transcript")
        order.attachments = [attachment]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.return_value = AttachmentType.TRANSCRIPT
            mock_att_mgr.get_preferred_format.return_value = "txt"
            mock_att_mgr.get_attachment_metadata.side_effect = Exception("Download failed")
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            assert "Failed" in result.output or "failures" in result.output.lower()

    def test_sync_with_order_error(self, monkeypatch, tmp_path):
        """Test sync with order processing error."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order

        order = Order(order_number="12345", status="Complete")

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager"), \
             patch("rev_exporter.cli.StorageManager"):

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.side_effect = Exception("Order error")
            mock_order_mgr_class.return_value = mock_order_mgr

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            assert "Failed" in result.output or "failures" in result.output.lower()

    def test_sync_summary_with_failures(self, monkeypatch, tmp_path):
        """Test sync summary output with failures."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order

        order = Order(order_number="12345", status="Complete")
        order.attachments = []

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager"), \
             patch("rev_exporter.cli.StorageManager"):

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            assert "SYNC SUMMARY" in result.output

    def test_sync_exclude_media(self, monkeypatch, tmp_path):
        """Test sync with media excluded."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        attachment = Attachment(id="att_001", name="audio.mp3", type="media")
        order.attachments = [attachment]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.return_value = AttachmentType.MEDIA
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports"), "--no-include-media"],
            )

            assert result.exit_code == 0
            # Media should be skipped
            mock_storage.save_attachment.assert_not_called()

    def test_sync_exclude_transcripts(self, monkeypatch, tmp_path):
        """Test sync with transcripts excluded."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        attachment = Attachment(id="att_001", name="transcript.txt", type="transcript")
        order.attachments = [attachment]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.return_value = AttachmentType.TRANSCRIPT
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports"), "--no-include-transcripts"],
            )

            assert result.exit_code == 0
            # Transcripts should be skipped
            mock_storage.save_attachment.assert_not_called()

    def test_sync_many_failures(self, monkeypatch, tmp_path):
        """Test sync summary with many failures (>10)."""
        monkeypatch.setenv("REV_CLIENT_API_KEY", "test_client")
        monkeypatch.setenv("REV_USER_API_KEY", "test_user")

        runner = CliRunner()

        from rev_exporter.models import Order, Attachment

        order = Order(order_number="12345", status="Complete")
        # Create 15 attachments that will all fail
        order.attachments = [
            Attachment(id=f"att_{i:03d}", name=f"file_{i}.txt", type="transcript")
            for i in range(15)
        ]

        with patch("rev_exporter.cli.OrderManager") as mock_order_mgr_class, \
             patch("rev_exporter.cli.AttachmentManager") as mock_att_mgr_class, \
             patch("rev_exporter.cli.StorageManager") as mock_storage_class:

            mock_order_mgr = Mock()
            mock_order_mgr.get_all_orders.return_value = [order]
            mock_order_mgr.filter_completed_orders.return_value = [order]
            mock_order_mgr.get_order_details.return_value = order
            mock_order_mgr_class.return_value = mock_order_mgr

            mock_att_mgr = Mock()
            mock_att_mgr.classify_attachment.return_value = AttachmentType.TRANSCRIPT
            mock_att_mgr.get_preferred_format.return_value = "txt"
            mock_att_mgr.get_attachment_metadata.side_effect = Exception("Download failed")
            mock_att_mgr_class.return_value = mock_att_mgr

            mock_storage = Mock()
            mock_storage.is_downloaded.return_value = False
            mock_storage_class.return_value = mock_storage

            result = runner.invoke(
                main,
                ["sync", "--output-dir", str(tmp_path / "exports")],
            )

            assert result.exit_code == 0
            # Should show "... and X more" message
            assert "... and" in result.output or "more" in result.output.lower()

