"""
WebSocket support for real-time features.

This module provides WebSocket endpoints for real-time collaboration,
including presence updates and event streaming.
"""

from .presence_ws import router as presence_router

__all__ = ["presence_router"]
