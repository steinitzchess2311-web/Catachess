"""
R2 storage client for PGN files.

Uses S3-compatible API (boto3) to interact with Cloudflare R2.
"""

import hashlib
from dataclasses import dataclass
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError


@dataclass
class R2Config:
    """
    R2 connection configuration.

    Attributes:
        endpoint: R2 endpoint URL
        access_key: Access key ID
        secret_key: Secret access key
        bucket: Bucket name
    """

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str


@dataclass
class UploadResult:
    """
    Result of R2 upload operation.

    Attributes:
        key: Object key in R2
        etag: ETag returned by R2
        size: Size of uploaded content in bytes
        content_hash: SHA-256 hash of content
    """

    key: str
    etag: str
    size: int
    content_hash: str


class R2Client:
    """
    Client for R2 storage operations.

    Provides methods to upload, download, and manage PGN files in R2.
    """

    def __init__(self, config: R2Config):
        """
        Initialize R2 client.

        Args:
            config: R2 configuration
        """
        self.config = config

        # Create S3 client with R2 endpoint
        self.s3 = boto3.client(
            "s3",
            endpoint_url=config.endpoint,
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name="auto",  # R2 uses "auto" region
        )

    def upload_pgn(
        self,
        key: str,
        content: str | bytes,
        content_type: str = "application/x-chess-pgn",
        metadata: dict[str, str] | None = None,
    ) -> UploadResult:
        """
        Upload PGN content to R2.

        Args:
            key: Object key (path in bucket)
            content: PGN content (string or bytes)
            content_type: MIME type
            metadata: Optional metadata dict

        Returns:
            UploadResult with upload details

        Raises:
            ClientError: If upload fails
        """
        # Convert string to bytes
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        # Calculate hash for integrity
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        size = len(content_bytes)

        # Prepare metadata
        upload_metadata = metadata or {}
        upload_metadata["content-hash"] = content_hash

        # Upload to R2
        response = self.s3.put_object(
            Bucket=self.config.bucket,
            Key=key,
            Body=content_bytes,
            ContentType=content_type,
            Metadata=upload_metadata,
        )

        return UploadResult(
            key=key,
            etag=response["ETag"].strip('"'),  # Remove quotes from ETag
            size=size,
            content_hash=content_hash,
        )

    def download_pgn(self, key: str) -> str:
        """
        Download PGN content from R2.

        Args:
            key: Object key

        Returns:
            PGN content as string

        Raises:
            ClientError: If download fails (e.g., key not found)
        """
        response = self.s3.get_object(
            Bucket=self.config.bucket,
            Key=key,
        )

        # Read and decode content
        content_bytes = response["Body"].read()
        return content_bytes.decode("utf-8")

    def download_pgn_bytes(self, key: str) -> bytes:
        """
        Download PGN content as bytes.

        Args:
            key: Object key

        Returns:
            PGN content as bytes
        """
        response = self.s3.get_object(
            Bucket=self.config.bucket,
            Key=key,
        )

        return response["Body"].read()

    def exists(self, key: str) -> bool:
        """
        Check if object exists in R2.

        Args:
            key: Object key

        Returns:
            True if object exists
        """
        try:
            self.s3.head_object(
                Bucket=self.config.bucket,
                Key=key,
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def delete(self, key: str) -> None:
        """
        Delete object from R2.

        Args:
            key: Object key

        Raises:
            ClientError: If deletion fails
        """
        self.s3.delete_object(
            Bucket=self.config.bucket,
            Key=key,
        )

    def get_metadata(self, key: str) -> dict[str, str]:
        """
        Get object metadata.

        Args:
            key: Object key

        Returns:
            Metadata dict

        Raises:
            ClientError: If object not found
        """
        response = self.s3.head_object(
            Bucket=self.config.bucket,
            Key=key,
        )

        return response.get("Metadata", {})

    def get_etag(self, key: str) -> str:
        """
        Get ETag for object.

        Args:
            key: Object key

        Returns:
            ETag string (without quotes)

        Raises:
            ClientError: If object not found
        """
        response = self.s3.head_object(
            Bucket=self.config.bucket,
            Key=key,
        )

        return response["ETag"].strip('"')

    def list_keys(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        """
        List object keys with optional prefix.

        Args:
            prefix: Key prefix filter
            max_keys: Maximum number of keys to return

        Returns:
            List of object keys
        """
        response = self.s3.list_objects_v2(
            Bucket=self.config.bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )

        if "Contents" not in response:
            return []

        return [obj["Key"] for obj in response["Contents"]]


def create_r2_client_from_env() -> R2Client:
    """
    Create R2 client from environment variables.

    Expected variables:
    - R2_ENDPOINT
    - R2_ACCESS_KEY
    - R2_SECRET_KEY
    - R2_BUCKET

    Returns:
        Configured R2Client

    Raises:
        ValueError: If required env vars are missing
    """
    import os

    endpoint = os.getenv("R2_ENDPOINT")
    access_key = os.getenv("R2_ACCESS_KEY")
    secret_key = os.getenv("R2_SECRET_KEY")
    bucket = os.getenv("R2_BUCKET")

    if not all([endpoint, access_key, secret_key, bucket]):
        raise ValueError(
            "Missing required R2 environment variables: "
            "R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET"
        )

    config = R2Config(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=bucket,
    )

    return R2Client(config)
