"""
File storage abstraction for handling file uploads.
Provides a consistent interface for local and cloud storage (S3, Azure, etc.).
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import uuid
from datetime import datetime


class FileStorageBackend(ABC):
    """
    Abstract base class for file storage implementations.
    Provides interface for saving, retrieving, and deleting files.
    """

    @abstractmethod
    def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> tuple[str, str]:
        """
        Save a file to storage.

        Args:
            file: File-like object to save
            filename: Original filename
            content_type: MIME type of the file
            metadata: Additional metadata to store with file

        Returns:
            Tuple of (storage_path, public_url)
        """
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            True if deleted successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_url(self, storage_path: str) -> str:
        """
        Get public URL for a file.

        Args:
            storage_path: Path to the file in storage

        Returns:
            Public URL to access the file
        """
        pass

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    def get_file_bytes(self, storage_path: str) -> bytes:
        """
        Download / read the raw bytes of a file from storage.

        Args:
            storage_path: Path to the file in storage

        Returns:
            File contents as bytes
        """
        pass

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent collisions.

        Args:
            original_filename: Original filename from user

        Returns:
            Unique filename with timestamp and UUID
        """
        # Get file extension
        ext = Path(original_filename).suffix
        # Generate unique name: timestamp_uuid_originalname
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        # Clean the original filename (remove extension)
        clean_name = Path(original_filename).stem
        # Sanitize filename
        clean_name = "".join(
            c for c in clean_name if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        clean_name = clean_name[:50]  # Limit length

        return f"{timestamp}_{unique_id}_{clean_name}{ext}"

    def save_at_path(
        self,
        file: BinaryIO,
        storage_path: str,
        content_type: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Save a file at an exact storage path (no auto-naming or date layout).

        Args:
            file: File-like object to save
            storage_path: Exact path where the file should be stored
            content_type: MIME type of the file

        Returns:
            Tuple of (storage_path, public_url)
        """
        raise NotImplementedError


class LocalFileStorage(FileStorageBackend):
    """
    Local filesystem storage implementation.
    Stores files in MEDIA_ROOT directory.
    """

    def __init__(self):
        self.storage = FileSystemStorage(
            location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL
        )
        self.base_path = "job_applications"

    def _get_storage_path(self, filename: str) -> str:
        """
        Generate organized storage path by date.

        Args:
            filename: Filename to store

        Returns:
            Relative path within storage (e.g., job_applications/2026/02/08/file.pdf)
        """
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        return f"{self.base_path}/{date_path}/{filename}"

    def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> tuple[str, str]:
        """
        Save file to local filesystem.

        Args:
            file: File-like object to save
            filename: Original filename
            content_type: MIME type (not used in local storage)
            metadata: Additional metadata (not used in local storage)

        Returns:
            Tuple of (storage_path, public_url)
        """
        # Generate unique filename
        unique_filename = self.generate_unique_filename(filename)

        # Get organized storage path
        storage_path = self._get_storage_path(unique_filename)

        # Save file
        saved_path = self.storage.save(storage_path, file)

        # Get public URL
        public_url = self.storage.url(saved_path)

        return saved_path, public_url

    def save_at_path(
        self,
        file: BinaryIO,
        storage_path: str,
        content_type: Optional[str] = None,
    ) -> tuple[str, str]:
        """Save file at an exact storage path."""
        saved_path = self.storage.save(storage_path, file)
        public_url = self.storage.url(saved_path)
        return saved_path, public_url

    def delete(self, storage_path: str) -> bool:
        """
        Delete file from local filesystem.

        Args:
            storage_path: Path to the file

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if self.storage.exists(storage_path):
                self.storage.delete(storage_path)
                return True
            return False
        except Exception as e:
            # Log error in production
            print(f"Error deleting file {storage_path}: {e}")
            return False

    def get_url(self, storage_path: str) -> str:
        """
        Get public URL for local file.

        Args:
            storage_path: Path to the file

        Returns:
            Public URL (e.g., /media/job_applications/2026/02/08/file.pdf)
        """
        return self.storage.url(storage_path)

    def exists(self, storage_path: str) -> bool:
        """
        Check if file exists in local filesystem.

        Args:
            storage_path: Path to the file

        Returns:
            True if file exists, False otherwise
        """
        return self.storage.exists(storage_path)

    def get_file_bytes(self, storage_path: str) -> bytes:
        """Read raw bytes from local filesystem."""
        full_path = Path(settings.MEDIA_ROOT) / storage_path
        return full_path.read_bytes()


class S3FileStorage(FileStorageBackend):
    """
    AWS S3 storage implementation using boto3.

    Required settings (via env vars):
      AWS_ACCESS_KEY_ID
      AWS_SECRET_ACCESS_KEY
      AWS_STORAGE_BUCKET_NAME
      AWS_S3_REGION_NAME
    """

    def __init__(self):
        import boto3
        from botocore.exceptions import NoCredentialsError

        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME
        self.base_path = "job_applications"

        if not self.bucket_name:
            raise ValueError("AWS_STORAGE_BUCKET_NAME is not configured.")

        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def _get_storage_path(self, filename: str) -> str:
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        return f"{self.base_path}/{date_path}/{filename}"

    def save(
        self,
        file: BinaryIO,
        filename: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> tuple[str, str]:
        """Upload file to S3 and return (s3_key, presigned_url)."""
        unique_filename = self.generate_unique_filename(filename)
        storage_path = self._get_storage_path(unique_filename)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}

        self.client.upload_fileobj(
            file, self.bucket_name, storage_path, ExtraArgs=extra_args
        )

        public_url = self.get_url(storage_path)
        return storage_path, public_url

    def save_at_path(
        self,
        file: BinaryIO,
        storage_path: str,
        content_type: Optional[str] = None,
    ) -> tuple[str, str]:
        """Save file at an exact S3 key."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        self.client.upload_fileobj(
            file, self.bucket_name, storage_path, ExtraArgs=extra_args
        )
        public_url = self.get_url(storage_path)
        return storage_path, public_url

    def delete(self, storage_path: str) -> bool:
        """Delete object from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=storage_path)
            return True
        except Exception as e:
            print(f"Error deleting S3 object {storage_path}: {e}")
            return False

    def get_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Return a presigned URL valid for `expires_in` seconds (default 1 hour)."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": storage_path},
            ExpiresIn=expires_in,
        )

    def exists(self, storage_path: str) -> bool:
        """Check if an S3 object exists."""
        from botocore.exceptions import ClientError

        try:
            self.client.head_object(Bucket=self.bucket_name, Key=storage_path)
            return True
        except ClientError:
            return False

    def get_file_bytes(self, storage_path: str) -> bytes:
        """Download raw bytes from S3."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=storage_path)
        return response["Body"].read()


# Storage backend factory
def get_storage_backend() -> FileStorageBackend:
    """
    Factory function to get the configured storage backend.

    Returns appropriate storage backend based on settings.STORAGE_BACKEND.

    Returns:
        Instance of FileStorageBackend (LocalFileStorage or S3FileStorage)
    """
    backend_type = getattr(settings, "STORAGE_BACKEND", "local").lower()

    if backend_type == "local":
        return LocalFileStorage()
    elif backend_type == "s3":
        return S3FileStorage()
    else:
        raise ValueError(
            f"Unknown storage backend: {backend_type}. Use 'local' or 's3'."
        )


# Singleton instance - created once and reused
_storage_instance: Optional[FileStorageBackend] = None


def get_storage() -> FileStorageBackend:
    """
    Get the singleton storage backend instance.

    Returns:
        Configured storage backend instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = get_storage_backend()
    return _storage_instance
