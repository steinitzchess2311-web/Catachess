"""
Storage Core - Infrastructure Layer

This module provides the foundational R2 storage infrastructure.
It is completely business-agnostic and knows nothing about:
- Games
- Users
- PGN
- Assignments

Exports:
- StorageClient: The only place that touches boto3
- StorageConfig: R2 connection configuration
- Storage exceptions: Custom error boundaries
"""
from storage.core.client import StorageClient
from storage.core.config import StorageConfig
from storage.core.errors import (
    StorageError,
    StorageUnavailable,
    ObjectNotFound,
    ObjectAlreadyExists,
    InvalidObjectKey,
)

__all__ = [
    "StorageClient",
    "StorageConfig",
    "StorageError",
    "StorageUnavailable",
    "ObjectNotFound",
    "ObjectAlreadyExists",
    "InvalidObjectKey",
]
