"""
Storage Client - Pure R2 Operations

Purpose:
    This is the ONLY file in the entire system that directly uses boto3.
    It provides a clean, minimal interface for object storage operations.

Key Principle:
    This client is completely business-agnostic. It doesn't know about:
    - PGN files
    - Game IDs
    - User IDs
    - Permissions

    It only knows how to:
    - Put bytes at a key
    - Get bytes from a key
    - Delete a key
    - Check if a key exists

Why this abstraction matters:
    - Easy to test (mock this client, not boto3)
    - Easy to switch providers (S3, GCS, Azure Blob)
    - Single point of failure/success for storage operations
    - Consistent error handling
"""
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError
from typing import BinaryIO

from storage.core.config import StorageConfig
from storage.core.errors import (
    StorageUnavailable,
    ObjectNotFound,
    InvalidObjectKey,
    StoragePermissionDenied,
    StorageError,
)


class StorageClient:
    """
    Pure R2 storage client.

    This class wraps boto3 S3 client for Cloudflare R2.
    All boto3 exceptions are caught and converted to storage exceptions.

    Attributes:
        config: Storage configuration
        _client: Internal boto3 S3 client (private)

    Example:
        >>> config = StorageConfig.from_env()
        >>> client = StorageClient(config)
        >>> client.put_object("test.txt", b"hello world")
        >>> content = client.get_object("test.txt")
        >>> print(content)
        b'hello world'
    """

    def __init__(self, config: StorageConfig):
        """
        Initialize storage client with configuration.

        Args:
            config: StorageConfig instance

        Raises:
            StorageUnavailable: If client initialization fails
        """
        self.config = config

        try:
            self._client = boto3.client(
                "s3",
                endpoint_url=config.endpoint,
                aws_access_key_id=config.access_key_id,
                aws_secret_access_key=config.secret_access_key,
                region_name=config.region,
            )
        except (NoCredentialsError, ClientError) as e:
            raise StorageUnavailable(
                reason="Failed to initialize storage client",
                details={"error": str(e)}
            )

    def put_object(
        self,
        key: str,
        content: bytes | BinaryIO,
        content_type: str | None = None,
    ) -> None:
        """
        Store an object in R2.

        This operation overwrites if the key already exists.
        It does NOT create directories - R2 is flat storage with key prefixes.

        Args:
            key: Object key (e.g., "games/abc123.pgn")
            content: Object content (bytes or file-like object)
            content_type: Optional MIME type (e.g., "application/x-chess-pgn")

        Raises:
            InvalidObjectKey: If key is invalid
            StorageUnavailable: If storage is unreachable
            StoragePermissionDenied: If operation not permitted
            StorageError: For other storage errors

        Example:
            >>> client.put_object("test.pgn", b"[Event \"Test\"]")
            >>> client.put_object("test.json", b'{"key": "value"}', "application/json")
        """
        self._validate_key(key)

        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self._client.put_object(
                Bucket=self.config.bucket,
                Key=key,
                Body=content,
                **extra_args
            )

        except EndpointConnectionError:
            raise StorageUnavailable(
                reason="Cannot connect to storage endpoint",
                details={"endpoint": self.config.endpoint}
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code in ("AccessDenied", "InvalidAccessKeyId"):
                raise StoragePermissionDenied(
                    operation="put_object",
                    reason=str(e)
                )

            raise StorageError(
                message=f"Failed to put object: {error_code}",
                details={"key": key, "error": str(e)}
            )

    def get_object(self, key: str) -> bytes:
        """
        Retrieve an object from R2.

        Args:
            key: Object key (e.g., "games/abc123.pgn")

        Returns:
            Object content as bytes

        Raises:
            InvalidObjectKey: If key is invalid
            ObjectNotFound: If object doesn't exist
            StorageUnavailable: If storage is unreachable
            StorageError: For other storage errors

        Example:
            >>> content = client.get_object("test.pgn")
            >>> print(content.decode('utf-8'))
            [Event "Test"]
        """
        self._validate_key(key)

        try:
            response = self._client.get_object(
                Bucket=self.config.bucket,
                Key=key
            )
            return response["Body"].read()

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "NoSuchKey":
                raise ObjectNotFound(key)

            if error_code in ("AccessDenied", "InvalidAccessKeyId"):
                raise StoragePermissionDenied(
                    operation="get_object",
                    reason=str(e)
                )

            raise StorageError(
                message=f"Failed to get object: {error_code}",
                details={"key": key, "error": str(e)}
            )
        except EndpointConnectionError:
            raise StorageUnavailable(
                reason="Cannot connect to storage endpoint",
                details={"endpoint": self.config.endpoint}
            )

    def delete_object(self, key: str) -> None:
        """
        Delete an object from R2.

        This operation is idempotent - deleting a non-existent key succeeds.

        Args:
            key: Object key (e.g., "games/abc123.pgn")

        Raises:
            InvalidObjectKey: If key is invalid
            StorageUnavailable: If storage is unreachable
            StoragePermissionDenied: If operation not permitted
            StorageError: For other storage errors

        Example:
            >>> client.delete_object("test.pgn")
            >>> # No error even if already deleted
            >>> client.delete_object("test.pgn")
        """
        self._validate_key(key)

        try:
            self._client.delete_object(
                Bucket=self.config.bucket,
                Key=key
            )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code in ("AccessDenied", "InvalidAccessKeyId"):
                raise StoragePermissionDenied(
                    operation="delete_object",
                    reason=str(e)
                )

            raise StorageError(
                message=f"Failed to delete object: {error_code}",
                details={"key": key, "error": str(e)}
            )
        except EndpointConnectionError:
            raise StorageUnavailable(
                reason="Cannot connect to storage endpoint",
                details={"endpoint": self.config.endpoint}
            )

    def exists(self, key: str) -> bool:
        """
        Check if an object exists in R2.

        This is more efficient than get_object() for existence checks.

        Args:
            key: Object key (e.g., "games/abc123.pgn")

        Returns:
            True if object exists, False otherwise

        Raises:
            InvalidObjectKey: If key is invalid
            StorageUnavailable: If storage is unreachable
            StorageError: For other storage errors

        Example:
            >>> client.put_object("test.pgn", b"content")
            >>> client.exists("test.pgn")
            True
            >>> client.exists("nonexistent.pgn")
            False
        """
        self._validate_key(key)

        try:
            self._client.head_object(
                Bucket=self.config.bucket,
                Key=key
            )
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "404":
                return False

            if error_code in ("AccessDenied", "InvalidAccessKeyId"):
                raise StoragePermissionDenied(
                    operation="exists",
                    reason=str(e)
                )

            raise StorageError(
                message=f"Failed to check object existence: {error_code}",
                details={"key": key, "error": str(e)}
            )
        except EndpointConnectionError:
            raise StorageUnavailable(
                reason="Cannot connect to storage endpoint",
                details={"endpoint": self.config.endpoint}
            )

    def _validate_key(self, key: str) -> None:
        """
        Validate object key format.

        Args:
            key: Object key to validate

        Raises:
            InvalidObjectKey: If key is invalid
        """
        if not key:
            raise InvalidObjectKey(key, "Key cannot be empty")

        if len(key) > 1024:
            raise InvalidObjectKey(key, "Key exceeds maximum length (1024)")

        # R2/S3 doesn't allow keys starting with /
        if key.startswith("/"):
            raise InvalidObjectKey(key, "Key cannot start with /")

    def __repr__(self) -> str:
        """String representation of client."""
        return f"StorageClient(bucket={self.config.bucket!r})"
