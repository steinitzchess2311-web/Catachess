"""
Storage Errors - Unified Error Boundaries

Purpose:
    Define storage-specific exceptions to isolate the rest of the application
    from boto3/R2 implementation details.

Key Principle:
    No other part of the system should ever catch boto3 exceptions directly.
    All storage errors should be caught and re-raised as these custom exceptions.

Why this matters:
    - If we switch from R2 to S3 or another provider, only storage/core changes
    - Business logic doesn't need to know about AWS/Cloudflare specifics
    - Consistent error handling across the application
"""


class StorageError(Exception):
    """
    Base exception for all storage-related errors.

    All storage exceptions should inherit from this to allow
    blanket error handling when needed.
    """
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class StorageUnavailable(StorageError):
    """
    Storage service is temporarily unavailable.

    Use cases:
    - R2 endpoint not reachable
    - Network timeout
    - Service maintenance
    - Rate limiting

    This is a transient error - retry might succeed.
    """
    def __init__(self, reason: str, details: dict | None = None):
        super().__init__(
            message=f"Storage service unavailable: {reason}",
            details=details or {}
        )


class ObjectNotFound(StorageError):
    """
    Requested object does not exist in storage.

    Use cases:
    - get_object() for non-existent key
    - delete_object() for non-existent key

    This is NOT an error in many cases (e.g., checking if object exists).
    """
    def __init__(self, key: str):
        super().__init__(
            message=f"Object not found: {key}",
            details={"key": key}
        )


class ObjectAlreadyExists(StorageError):
    """
    Object already exists and operation requires uniqueness.

    Use cases:
    - put_object() with overwrite=False
    - Creating unique objects

    Note: Not used for normal put_object() which overwrites by default.
    """
    def __init__(self, key: str):
        super().__init__(
            message=f"Object already exists: {key}",
            details={"key": key}
        )


class InvalidObjectKey(StorageError):
    """
    Object key is invalid or malformed.

    Use cases:
    - Empty key
    - Key with invalid characters
    - Key exceeding length limits

    This indicates a programming error, not a transient failure.
    """
    def __init__(self, key: str, reason: str):
        super().__init__(
            message=f"Invalid object key '{key}': {reason}",
            details={"key": key, "reason": reason}
        )


class StoragePermissionDenied(StorageError):
    """
    Insufficient permissions to perform operation.

    Use cases:
    - Invalid credentials
    - Bucket access denied
    - Object ACL restrictions

    This indicates a configuration error, not a transient failure.
    """
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Permission denied for {operation}: {reason}",
            details={"operation": operation, "reason": reason}
        )
