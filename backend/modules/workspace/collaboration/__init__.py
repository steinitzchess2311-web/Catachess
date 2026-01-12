"""
Collaboration module for real-time user presence and coordination.

This module provides the infrastructure for tracking user presence,
managing heartbeats, and coordinating collaborative editing.
"""

from .presence_manager import PresenceManager

__all__ = ["PresenceManager"]
