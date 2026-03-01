"""
Temporary file storage service for Railway deployment.

Handles:
- Storing generated files temporarily
- File retrieval for download
- Automatic cleanup of expired files
"""

import os
import uuid
import logging
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Storage configuration
# On Railway, use /tmp for ephemeral storage
# Files should be downloaded within TTL before pod restarts
STORAGE_DIR = os.getenv("FILE_STORAGE_DIR", "/tmp/valuation-files")
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", "3600"))  # 1 hour default


class FileStorage:
    """
    Temporary file storage for generated documents.

    Note: Railway uses ephemeral storage. Files are lost on pod restart.
    For persistence, consider S3/R2 in the future.
    """

    @staticmethod
    def _ensure_storage_dir():
        """Ensure the storage directory exists."""
        os.makedirs(STORAGE_DIR, exist_ok=True)

    @staticmethod
    def _generate_file_id() -> str:
        """Generate a unique file ID."""
        return str(uuid.uuid4())

    @staticmethod
    def store_file(
        content: bytes,
        filename: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Store a file and return its path/ID.

        Args:
            content: File content as bytes
            filename: Original filename
            content_type: MIME type

        Returns:
            File ID/path for retrieval
        """
        FileStorage._ensure_storage_dir()

        file_id = FileStorage._generate_file_id()

        # Get file extension from original filename
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = ".bin"

        # Store file with UUID name to prevent conflicts
        stored_filename = f"{file_id}{ext}"
        file_path = os.path.join(STORAGE_DIR, stored_filename)

        # Write file
        with open(file_path, 'wb') as f:
            f.write(content)

        # Store metadata in a companion file
        metadata_path = f"{file_path}.meta"
        with open(metadata_path, 'w') as f:
            f.write(f"filename={filename}\n")
            f.write(f"content_type={content_type}\n")
            f.write(f"created_at={datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"ttl_seconds={FILE_TTL_SECONDS}\n")

        logger.info(f"Stored file {file_id} ({filename})")
        return file_id

    @staticmethod
    def get_file(file_id: str) -> Optional[Tuple[bytes, str, str]]:
        """
        Retrieve a file by ID.

        Args:
            file_id: File ID from store_file

        Returns:
            Tuple of (content, filename, content_type) or None if not found
        """
        FileStorage._ensure_storage_dir()

        # Find file with matching ID
        for filename in os.listdir(STORAGE_DIR):
            if filename.startswith(file_id) and not filename.endswith('.meta'):
                file_path = os.path.join(STORAGE_DIR, filename)
                metadata_path = f"{file_path}.meta"

                # Check if file exists
                if not os.path.exists(file_path):
                    return None

                # Check TTL
                if FileStorage._is_expired(file_path):
                    logger.warning(f"File {file_id} has expired")
                    # Still return file, cleanup will handle deletion
                    # This allows a small grace period for ongoing downloads

                # Read metadata
                original_filename = filename
                content_type = "application/octet-stream"

                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        for line in f:
                            if line.startswith("filename="):
                                original_filename = line.strip().split("=", 1)[1]
                            elif line.startswith("content_type="):
                                content_type = line.strip().split("=", 1)[1]

                # Read content
                with open(file_path, 'rb') as f:
                    content = f.read()

                return content, original_filename, content_type

        logger.warning(f"File {file_id} not found")
        return None

    @staticmethod
    def delete_file(file_id: str) -> bool:
        """
        Delete a file by ID.

        Args:
            file_id: File ID to delete

        Returns:
            True if deleted, False if not found
        """
        FileStorage._ensure_storage_dir()

        deleted = False

        for filename in os.listdir(STORAGE_DIR):
            if filename.startswith(file_id):
                file_path = os.path.join(STORAGE_DIR, filename)
                try:
                    os.remove(file_path)
                    deleted = True
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")

        if deleted:
            logger.info(f"Deleted file {file_id}")

        return deleted

    @staticmethod
    def _is_expired(file_path: str) -> bool:
        """
        Check if a file has expired based on its metadata.

        Args:
            file_path: Path to the file

        Returns:
            True if expired, False otherwise
        """
        metadata_path = f"{file_path}.meta"

        if not os.path.exists(metadata_path):
            # No metadata, use file modification time
            mtime = os.path.getmtime(file_path)
            created_at = datetime.fromtimestamp(mtime)
            ttl = FILE_TTL_SECONDS
        else:
            # Read from metadata
            created_at = None
            ttl = FILE_TTL_SECONDS

            with open(metadata_path, 'r') as f:
                for line in f:
                    if line.startswith("created_at="):
                        try:
                            created_at = datetime.fromisoformat(line.strip().split("=", 1)[1])
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Failed to parse created_at from metadata: {e}")
                    elif line.startswith("ttl_seconds="):
                        try:
                            ttl = int(line.strip().split("=", 1)[1])
                        except (ValueError, IndexError) as e:
                            logger.warning(f"Failed to parse ttl_seconds from metadata: {e}")

            if created_at is None:
                mtime = os.path.getmtime(file_path)
                created_at = datetime.fromtimestamp(mtime)

        expiry = created_at + timedelta(seconds=ttl)
        return datetime.now(timezone.utc) > expiry

    @staticmethod
    def cleanup_expired_files() -> int:
        """
        Delete all expired files.

        Returns:
            Number of files deleted
        """
        FileStorage._ensure_storage_dir()

        deleted_count = 0
        files_to_delete = []

        # Find expired files
        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith('.meta'):
                continue

            file_path = os.path.join(STORAGE_DIR, filename)

            if FileStorage._is_expired(file_path):
                # Extract file ID from filename
                file_id = filename.split('.')[0]
                files_to_delete.append(file_id)

        # Delete expired files
        for file_id in files_to_delete:
            if FileStorage.delete_file(file_id):
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired files")

        return deleted_count

    @staticmethod
    def get_storage_stats() -> dict:
        """
        Get storage statistics.

        Returns:
            Dict with storage stats
        """
        FileStorage._ensure_storage_dir()

        total_size = 0
        file_count = 0
        expired_count = 0

        for filename in os.listdir(STORAGE_DIR):
            if filename.endswith('.meta'):
                continue

            file_path = os.path.join(STORAGE_DIR, filename)
            total_size += os.path.getsize(file_path)
            file_count += 1

            if FileStorage._is_expired(file_path):
                expired_count += 1

        return {
            "storage_dir": STORAGE_DIR,
            "file_count": file_count,
            "expired_count": expired_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }


# Export
__all__ = ['FileStorage']
