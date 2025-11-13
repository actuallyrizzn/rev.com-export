"""
End-to-end tests for Rev Exporter.

These tests run the full CLI workflow and require real API credentials.
Tests are skipped if credentials are not available.
"""

import os
import pytest
from pathlib import Path
from click.testing import CliRunner

from rev_exporter.cli import main


# Skip all e2e tests if credentials not available
pytestmark = pytest.mark.skipif(
    not (
        os.getenv("REV_CLIENT_API_KEY") and os.getenv("REV_USER_API_KEY")
    ),
    reason="E2E tests require REV_CLIENT_API_KEY and REV_USER_API_KEY",
)


class TestE2E:
    """End-to-end tests."""

    def test_test_connection_command(self):
        """Test the test-connection CLI command."""
        runner = CliRunner()
        result = runner.invoke(main, ["test-connection"])
        assert result.exit_code == 0
        assert "successful" in result.output.lower()

    def test_sync_dry_run(self, tmp_path):
        """Test sync command in dry-run mode."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "sync",
                "--output-dir", str(tmp_path / "exports"),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    @pytest.mark.slow
    def test_sync_small_batch(self, tmp_path):
        """Test sync command with a small batch (first page only)."""
        # This test actually downloads files, so mark as slow
        runner = CliRunner()
        
        # Use --since to limit scope if possible
        result = runner.invoke(
            main,
            [
                "sync",
                "--output-dir", str(tmp_path / "exports"),
                "--since", "2024-01-01",  # Adjust date as needed
            ],
        )
        
        # Should complete successfully (even if no orders found)
        assert result.exit_code == 0
        
        # Check that output directory structure exists
        exports_dir = tmp_path / "exports"
        if exports_dir.exists():
            # Verify structure if any orders were processed
            order_dirs = [d for d in exports_dir.iterdir() if d.is_dir()]
            for order_dir in order_dirs:
                # Check for expected subdirectories
                assert (order_dir / "media").exists() or \
                       (order_dir / "transcripts").exists() or \
                       (order_dir / "other").exists()
                # Check for metadata file
                assert (order_dir / "attachments.json").exists()

    def test_sync_with_flags(self, tmp_path):
        """Test sync command with various flag combinations."""
        runner = CliRunner()
        
        # Test with --no-include-media
        result = runner.invoke(
            main,
            [
                "sync",
                "--output-dir", str(tmp_path / "exports"),
                "--no-include-media",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

        # Test with --no-include-transcripts
        result = runner.invoke(
            main,
            [
                "sync",
                "--output-dir", str(tmp_path / "exports"),
                "--no-include-transcripts",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0

