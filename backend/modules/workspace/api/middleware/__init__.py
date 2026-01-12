"""
API middleware for cross-cutting concerns.

This module provides middleware for:
- Idempotency handling
- Request/response logging
- Error handling
"""

from .idempotency import IdempotencyMiddleware

__all__ = ["IdempotencyMiddleware"]
