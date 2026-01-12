"""
Infrastructure layer for cross-cutting concerns.

This module provides infrastructure services such as:
- Idempotency handling
- Caching
- External service integrations
"""

from .idempotency import IdempotencyService

__all__ = ["IdempotencyService"]
