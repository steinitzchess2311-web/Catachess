"""
Idempotency middleware for FastAPI.

Automatically handles idempotent requests using X-Idempotency-Key header.
"""

import json
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling idempotent requests.

    Features:
    - Checks for X-Idempotency-Key header
    - Returns cached response if key exists
    - Caches response for future requests with same key
    - Only applies to idempotent methods (POST, PUT, PATCH)
    """

    # Methods that support idempotency
    IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}

    # Paths that should use idempotency
    # Can be configured to include/exclude specific paths
    IDEMPOTENT_PATHS = [
        "/studies",
        "/discussions",
        "/export",
        "/share",
        "/nodes",
    ]

    def __init__(self, app, idempotency_service_factory: Callable):
        """
        Initialize middleware.

        Args:
            app: FastAPI application
            idempotency_service_factory: Factory function to create IdempotencyService
        """
        super().__init__(app)
        self.idempotency_service_factory = idempotency_service_factory

    async def dispatch(self, request: Request, call_next):
        """
        Process request with idempotency handling.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response (cached or fresh)
        """
        # Check if this request should use idempotency
        if not self._should_use_idempotency(request):
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("X-Idempotency-Key")

        if not idempotency_key:
            # No idempotency key provided, process normally
            return await call_next(request)

        # Get idempotency service
        # Note: This requires proper dependency injection setup
        # For now, this is a placeholder
        try:
            idempotency_service = await self.idempotency_service_factory(request)
        except Exception as e:
            logger.warning(f"Could not create idempotency service: {e}")
            return await call_next(request)

        # Check if we have a cached result
        cached_result = await idempotency_service.check_idempotency_key(idempotency_key)

        if cached_result is not None:
            # Return cached response
            logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
            return JSONResponse(
                content=cached_result.get("body"),
                status_code=cached_result.get("status_code", 200),
                headers=cached_result.get("headers", {})
            )

        # Process request normally
        response = await call_next(request)

        # Cache the response if successful (2xx status code)
        if 200 <= response.status_code < 300:
            try:
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                # Parse JSON body
                body_json = json.loads(body.decode())

                # Cache the result
                cache_data = {
                    "body": body_json,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }

                await idempotency_service.cache_idempotency_result(
                    key=idempotency_key,
                    result=cache_data
                )

                logger.info(f"Cached response for idempotency key: {idempotency_key}")

                # Return new response with body
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            except Exception as e:
                logger.error(f"Error caching idempotent response: {e}")
                # Return original response even if caching fails
                return response

        return response

    def _should_use_idempotency(self, request: Request) -> bool:
        """
        Check if request should use idempotency.

        Args:
            request: HTTP request

        Returns:
            True if idempotency should be used
        """
        # Check method
        if request.method not in self.IDEMPOTENT_METHODS:
            return False

        # Check path (simple prefix match)
        path = request.url.path
        for idempotent_path in self.IDEMPOTENT_PATHS:
            if path.startswith(idempotent_path):
                return True

        return False


# Decorator for marking endpoints as idempotent
def idempotent(ttl_seconds: int = 86400):
    """
    Decorator to mark an endpoint as idempotent.

    This is mainly for documentation purposes. The actual idempotency
    handling is done by the middleware.

    Args:
        ttl_seconds: Time-to-live for cached results (default: 24 hours)

    Example:
        @router.post("/studies")
        @idempotent(ttl_seconds=3600)
        async def create_study(...):
            ...
    """
    def decorator(func):
        func._idempotent = True
        func._idempotent_ttl = ttl_seconds
        return func
    return decorator
