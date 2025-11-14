"""
Scan export directory and build complete index of orders and files.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class FileScanner:
    """Scans export directory and builds index of all orders and files."""

    def __init__(self, export_dir: Path):
        """
        Initialize scanner.

        Args:
            export_dir: Path to export directory
        """
        self.export_dir = Path(export_dir)

    def scan(self) -> List[Dict[str, Any]]:
        """
        Scan export directory and return list of orders with all files.

        Returns:
            List of order dictionaries with complete file information
        """
        orders = []

        if not self.export_dir.exists():
            return orders

        for order_dir in sorted(self.export_dir.iterdir()):
            if not order_dir.is_dir() or order_dir.name.startswith(".") or order_dir.name == "files":
                continue

            order_number = order_dir.name

            # Read metadata
            metadata_file = order_dir / "attachments.json"
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                except Exception:
                    pass

            # Scan files in each subdirectory
            media_files = self._scan_directory(order_dir / "media", "media")
            transcript_files = self._scan_directory(order_dir / "transcripts", "transcript")
            other_files = self._scan_directory(order_dir / "other", "other")

            # Build file hash for unique identification
            file_hash = self._hash_order(order_number)

            orders.append(
                {
                    "order_number": order_number,
                    "status": metadata.get("status", "Unknown"),
                    "placed_on": metadata.get("placed_on"),
                    "attachments": metadata.get("attachments", []),
                    "media_files": media_files,
                    "transcript_files": transcript_files,
                    "other_files": other_files,
                    "file_hash": file_hash,
                }
            )

        return orders

    def _scan_directory(self, directory: Path, file_type: str) -> List[Dict[str, Any]]:
        """
        Scan a directory and return list of files with metadata.

        Args:
            directory: Directory to scan
            file_type: Type of files (media, transcript, other)

        Returns:
            List of file dictionaries
        """
        files = []

        if not directory.exists():
            return files

        for file_path in sorted(directory.iterdir()):
            if not file_path.is_file():
                continue

            # Skip metadata files
            if file_path.name == "attachments.json":
                continue

            # Determine if file is viewable
            is_viewable = self._is_viewable(file_path)

            # Generate file hash for unique identification
            file_hash = self._hash_file(file_path)

            # Get real extension (handles double extensions)
            real_ext = self._get_real_extension(file_path)
            
            # Use forward slashes for web paths (works on all platforms)
            relative_path = file_path.relative_to(self.export_dir)
            web_path = str(relative_path).replace("\\", "/")
            
            files.append(
                {
                    "name": file_path.name,
                    "path": web_path,
                    "size": file_path.stat().st_size,
                    "extension": real_ext,
                    "is_viewable": is_viewable,
                    "file_hash": file_hash,
                }
            )

        return files

    def _get_real_extension(self, file_path: Path) -> str:
        """
        Get the real file extension, handling double extensions.

        Args:
            file_path: Path to file

        Returns:
            Real file extension (e.g., .docx, .srt, .txt)
        """
        name = file_path.name.lower()
        # Known content file extensions (preferred)
        content_extensions = [".docx", ".srt", ".txt"]
        # Metadata extensions (should be ignored if content extension exists)
        metadata_extensions = [".json"]
        
        # Check for double extensions (e.g., .srt.srt, .docx.json)
        # First check for content extension followed by same extension
        for ext in content_extensions:
            if name.endswith(ext + ext):
                return ext
        
        # Check for content extension followed by metadata extension (e.g., .docx.json)
        for content_ext in content_extensions:
            for meta_ext in metadata_extensions:
                if name.endswith(content_ext + meta_ext):
                    return content_ext
        
        # Check for content extension followed by different content extension
        for ext1 in content_extensions:
            for ext2 in content_extensions:
                if ext1 != ext2 and name.endswith(ext1 + ext2):
                    # Prefer the first one
                    return ext1
        
        # If no double extension found, check if it's a single content extension
        for ext in content_extensions:
            if name.endswith(ext):
                return ext
        
        # Fall back to last extension
        return file_path.suffix.lower()

    def _is_viewable(self, file_path: Path) -> bool:
        """
        Check if file can be viewed in browser.

        Args:
            file_path: Path to file

        Returns:
            True if file can be viewed
        """
        name_lower = file_path.name.lower()
        
        # If file ends in .json, check if it's actually JSON content or metadata
        # Files like .docx.json are JSON transcript data and should be viewable
        if name_lower.endswith('.json'):
            # Check if it's a double extension (e.g., .docx.json, .srt.json)
            # These are JSON transcript data, not metadata files
            if any(name_lower.endswith(ext + '.json') for ext in ['.docx', '.srt', '.txt', '.mp4', '.m4a', '.mp3']):
                return True
            # Otherwise it's a metadata file, not viewable
            return False
        
        ext = self._get_real_extension(file_path)
        # Only viewable file types
        viewable_extensions = {".docx", ".txt", ".srt"}
        return ext in viewable_extensions

    def _hash_order(self, order_number: str) -> str:
        """Generate hash for order number."""
        return hashlib.md5(order_number.encode()).hexdigest()[:8]

    def _hash_file(self, file_path: Path) -> str:
        """Generate hash for file path."""
        path_str = str(file_path.relative_to(self.export_dir))
        return hashlib.md5(path_str.encode()).hexdigest()[:12]

