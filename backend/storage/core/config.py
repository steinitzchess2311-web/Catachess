"""
Storage Configuration - R2 Connection Settings

Purpose:
    Centralized configuration for Cloudflare R2 storage.
    Reads from environment variables for deployment flexibility.

Key Principle:
    This file knows about R2/S3, but nothing about:
    - What data is being stored
    - Who is storing it
    - Why it's being stored

Environment Variables Required:
    R2_ENDPOINT: Cloudflare R2 endpoint URL
    R2_BUCKET: Bucket name
    R2_ACCESS_KEY_ID: R2 API access key
    R2_SECRET_ACCESS_KEY: R2 API secret key
    R2_ACCOUNT_ID: Cloudflare account ID (optional, for logging)
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageConfig:
    """
    Immutable configuration for R2 storage.

    All values are read from environment variables on initialization.
    The frozen=True ensures configuration cannot be modified after creation.

    Attributes:
        endpoint: R2 endpoint URL (e.g., https://<account-id>.r2.cloudflarestorage.com)
        bucket: Bucket name (e.g., catachess-data)
        access_key_id: R2 API access key ID
        secret_access_key: R2 API secret access key
        region: AWS region (use 'auto' for R2)
        account_id: Cloudflare account ID (optional, for logging/debugging)
    """
    endpoint: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region: str = "auto"
    account_id: str | None = None

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """
        Create configuration from environment variables.

        This is the recommended way to create config in production.

        Returns:
            StorageConfig instance

        Raises:
            ValueError: If required environment variables are missing

        Example:
            >>> config = StorageConfig.from_env()
            >>> print(config.bucket)
            catachess-data
        """
        required_vars = {
            "R2_ENDPOINT": "endpoint",
            "R2_BUCKET": "bucket",
            "R2_ACCESS_KEY_ID": "access_key_id",
            "R2_SECRET_ACCESS_KEY": "secret_access_key",
        }

        config_dict = {}
        missing_vars = []

        for env_var, config_key in required_vars.items():
            value = os.getenv(env_var)
            if not value:
                missing_vars.append(env_var)
            else:
                config_dict[config_key] = value

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

        # Optional variables
        config_dict["region"] = os.getenv("R2_REGION", "auto")
        config_dict["account_id"] = os.getenv("R2_ACCOUNT_ID")

        return cls(**config_dict)

    @classmethod
    def for_testing(
        cls,
        endpoint: str = "http://localhost:9000",
        bucket: str = "test-bucket",
        access_key_id: str = "test-access-key",
        secret_access_key: str = "test-secret-key",
    ) -> "StorageConfig":
        """
        Create configuration for testing (e.g., with MinIO or localstack).

        This should only be used in tests, never in production.

        Args:
            endpoint: Test endpoint (default: localhost MinIO)
            bucket: Test bucket name
            access_key_id: Test access key
            secret_access_key: Test secret key

        Returns:
            StorageConfig instance for testing

        Example:
            >>> config = StorageConfig.for_testing()
            >>> client = StorageClient(config)
        """
        return cls(
            endpoint=endpoint,
            bucket=bucket,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region="auto",
        )

    def __repr__(self) -> str:
        """
        Safe string representation that doesn't expose secrets.

        Returns:
            String representation with masked credentials
        """
        return (
            f"StorageConfig("
            f"endpoint={self.endpoint!r}, "
            f"bucket={self.bucket!r}, "
            f"access_key_id={'*' * 8}, "
            f"secret_access_key={'*' * 8}, "
            f"region={self.region!r}"
            ")"
        )
