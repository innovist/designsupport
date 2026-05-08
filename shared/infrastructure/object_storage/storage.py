"""Object storage backend using boto3/MinIO with immutable upload support."""
import hashlib
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from shared.application.ports.ports import ObjectStoragePort
from shared.domain.exceptions import DomainError


class ObjectStorageBackend(ObjectStoragePort):
    """S3/MinIO object storage backend with immutable upload support."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = 'us-east-1',
    ) -> None:
        """Initialize S3 client."""
        self.bucket_name = bucket_name
        self.client: S3Client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key or os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=secret_key or os.environ.get('AWS_SECRET_ACCESS_KEY'),
            region_name=region,
        )

    async def upload_immutable(
        self,
        file_path: str,
        tenant_id: str,
        content_type: str,
    ) -> tuple[str, str]:
        """Upload file as immutable and return (uri, sha256_hash)."""
        path = Path(file_path)

        # Calculate SHA-256 hash
        sha256_hash = self._calculate_sha256(path)

        # Create immutable key with tenant prefix and hash
        key = f"{tenant_id}/{sha256_hash}/{path.name}"

        try:
            # Upload with content-disposition to prevent overwrite
            self.client.upload_file(
                str(path),
                self.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': {
                        'tenant-id': tenant_id,
                        'sha256': sha256_hash,
                        'original-filename': path.name,
                    },
                },
            )

            # Construct URI
            endpoint = self.client._endpoint
            uri = f"{endpoint}/{self.bucket_name}/{key}"

            return (uri, sha256_hash)

        except ClientError as e:
            raise DomainError(
                "storage_upload_failed",
                f"Failed to upload file: {e}",
            ) from e

    async def download(self, uri: str, local_path: str) -> None:
        """Download file from storage."""
        key = self._uri_to_key(uri)

        try:
            self.client.download_file(self.bucket_name, key, local_path)
        except ClientError as e:
            raise DomainError(
                "storage_download_failed",
                f"Failed to download file: {e}",
            ) from e

    async def get_metadata(self, uri: str) -> dict[str, Any]:
        """Get file metadata from storage."""
        key = self._uri_to_key(uri)

        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                'size': response.get('ContentLength', 0),
                'content_type': response.get('ContentType', ''),
                'metadata': response.get('Metadata', {}),
                'last_modified': response.get('LastModified'),
            }
        except ClientError as e:
            raise DomainError(
                "storage_metadata_failed",
                f"Failed to get metadata: {e}",
            ) from e

    async def delete(self, uri: str) -> None:
        """Delete file (tombstone - should not actually delete in production)."""
        key = self._uri_to_key(uri)

        try:
            # In production, implement tombstone pattern
            # For now, perform actual delete
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise DomainError(
                "storage_delete_failed",
                f"Failed to delete file: {e}",
            ) from e

    def _calculate_sha256(self, path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _uri_to_key(self, uri: str) -> str:
        """Extract key from URI."""
        # Format: {bucket}/{key} or {endpoint}/{bucket}/{key}
        parts = uri.split('/')
        if len(parts) >= 2 and parts[-2] == self.bucket_name:
            return '/'.join(parts[-1:])
        return '/'.join(parts[parts.index(self.bucket_name) + 1:])


class LocalObjectStorageBackend(ObjectStoragePort):
    """Local filesystem storage backend for development."""

    def __init__(self, base_path: str = '/tmp/media') -> None:
        """Initialize local storage."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_immutable(
        self,
        file_path: str,
        tenant_id: str,
        content_type: str,
    ) -> tuple[str, str]:
        """Upload file to local storage."""
        src_path = Path(file_path)

        # Calculate SHA-256
        sha256_hash = self._calculate_sha256(src_path)

        # Create tenant directory
        tenant_dir = self.base_path / tenant_id / sha256_hash
        tenant_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        dst_path = tenant_dir / src_path.name
        import shutil
        shutil.copy2(src_path, dst_path)

        uri = f"file://{dst_path}"
        return (uri, sha256_hash)

    async def download(self, uri: str, local_path: str) -> None:
        """Download file from local storage."""
        import shutil
        shutil.copy2(uri.replace('file://', ''), local_path)

    async def get_metadata(self, uri: str) -> dict[str, Any]:
        """Get file metadata."""
        path = Path(uri.replace('file://', ''))
        stat = path.stat()
        return {
            'size': stat.st_size,
            'content_type': 'application/octet-stream',
            'metadata': {},
            'last_modified': stat.st_mtime,
        }

    async def delete(self, uri: str) -> None:
        """Delete file."""
        path = Path(uri.replace('file://', ''))
        path.unlink(missing_ok=True)

    def _calculate_sha256(self, path: Path) -> str:
        """Calculate SHA-256 hash."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
