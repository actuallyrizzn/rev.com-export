"""
Main generator that orchestrates browser generation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
import webbrowser

from rev_exporter.browser.file_scanner import FileScanner
from rev_exporter.browser.templates import (
    generate_index,
    generate_order_detail,
    generate_file_viewer,
)

logger = logging.getLogger(__name__)


def generate_browser(export_dir: Path, open_browser: bool = True) -> None:
    """
    Generate static HTML browser for export directory.

    Args:
        export_dir: Path to export directory
        open_browser: Whether to open index.html in browser after generation
    """
    export_dir = Path(export_dir)

    if not export_dir.exists():
        raise ValueError(f"Export directory does not exist: {export_dir}")

    logger.info(f"Scanning export directory: {export_dir}")

    # Scan directory
    scanner = FileScanner(export_dir)
    orders = scanner.scan()

    if not orders:
        logger.warning("No orders found in export directory")
        return

    logger.info(f"Found {len(orders)} orders")

    # Create files directory for file viewer pages
    files_dir = export_dir / "files"
    files_dir.mkdir(exist_ok=True)

    # Generate index.html
    logger.info("Generating index.html...")
    index_html = generate_index(orders, str(export_dir))
    index_path = export_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_html)
    logger.info(f"Generated {index_path}")

    # Generate order detail pages
    for order in orders:
        logger.info(f"Generating order page for {order['order_number']}...")
        order_html = generate_order_detail(order, str(export_dir))
        order_path = export_dir / f"order_{order['file_hash']}.html"
        with open(order_path, "w", encoding="utf-8") as f:
            f.write(order_html)

        # Generate file viewer pages for all files
        all_files = (
            order["media_files"] + order["transcript_files"] + order["other_files"]
        )

        for file_info in all_files:
            if file_info.get("is_viewable", False):
                # Sanitize filename for logging (handle Unicode)
                safe_name = file_info['name'].encode('ascii', 'replace').decode('ascii')
                logger.debug(f"Generating file viewer for {safe_name}...")
                file_html = generate_file_viewer(
                    file_info, order["file_hash"], str(export_dir)
                )
                file_path = files_dir / f"file_{file_info['file_hash']}.html"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_html)

    logger.info("Browser generation complete!")

    # Open browser if requested
    if open_browser:
        index_url = index_path.as_uri()
        logger.info(f"Opening {index_url} in browser...")
        webbrowser.open(index_url)

