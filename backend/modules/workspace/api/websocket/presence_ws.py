"""
WebSocket endpoint for real-time presence updates.

Provides WebSocket connection for receiving real-time presence events
and maintaining active sessions through WebSocket keepalive.
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from workspace.events.bus import EventBus
from workspace.events.types import EventType

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for presence updates.

    Tracks active connections per study and broadcasts presence events
    to connected clients.
    """

    def __init__(self):
        """Initialize connection manager."""
        # study_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, study_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            study_id: Study ID to subscribe to
        """
        await websocket.accept()

        async with self._lock:
            if study_id not in self.active_connections:
                self.active_connections[study_id] = set()
            self.active_connections[study_id].add(websocket)

        logger.info(f"WebSocket connected for study {study_id}. "
                   f"Total connections: {len(self.active_connections.get(study_id, set()))}")

    async def disconnect(self, websocket: WebSocket, study_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            study_id: Study ID
        """
        async with self._lock:
            if study_id in self.active_connections:
                self.active_connections[study_id].discard(websocket)
                if not self.active_connections[study_id]:
                    del self.active_connections[study_id]

        logger.info(f"WebSocket disconnected for study {study_id}")

    async def broadcast_to_study(self, study_id: str, message: dict):
        """
        Broadcast a message to all connections for a study.

        Args:
            study_id: Study ID
            message: Message to broadcast
        """
        if study_id not in self.active_connections:
            return

        connections = self.active_connections[study_id].copy()
        disconnected = set()

        for websocket in connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(message)
                else:
                    disconnected.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    self.active_connections[study_id].discard(ws)
                if not self.active_connections[study_id]:
                    del self.active_connections[study_id]


# Global connection manager
manager = ConnectionManager()


async def subscribe_to_presence_events(event_bus: EventBus, study_id: str):
    """
    Subscribe to presence events for a study and broadcast them via WebSocket.

    This is a simplified version. In production, you'd want a more
    robust event subscription mechanism.

    Args:
        event_bus: Event bus instance
        study_id: Study ID to subscribe to
    """
    # This is a placeholder for event subscription
    # In a real implementation, you'd register a callback with the event bus
    pass


@router.websocket("/ws/presence")
async def presence_websocket(
    websocket: WebSocket,
    study_id: str = Query(..., description="Study ID to subscribe to"),
):
    """
    WebSocket endpoint for real-time presence updates.

    Clients connect to this endpoint to receive real-time updates about
    user presence in a study (join/leave/status changes/cursor moves).

    Query Parameters:
        study_id: Study ID to subscribe to

    WebSocket Protocol:
        - Client sends: heartbeat pings every 30s (optional, handled by HTTP endpoint too)
        - Server sends: presence events in JSON format

    Event format:
        {
            "type": "presence.user_joined" | "presence.user_left" | "presence.user_active" | ...,
            "data": {
                "user_id": "user123",
                "session_id": "session456",
                "status": "active",
                "chapter_id": "chapter789",
                "move_path": "main.12.var2.3",
                "timestamp": "2026-01-12T14:30:00Z"
            }
        }

    Args:
        websocket: WebSocket connection
        study_id: Study ID to monitor
    """
    await manager.connect(websocket, study_id)

    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection.established",
            "data": {
                "study_id": study_id,
                "timestamp": datetime.now(UTC).isoformat()
            }
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for client messages (e.g., ping/pong for keepalive)
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0  # 60s timeout
                )

                # Handle client messages
                if data.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "data": {"timestamp": datetime.now(UTC).isoformat()}
                    })

            except asyncio.TimeoutError:
                # No message received in 60s, send keepalive
                await websocket.send_json({
                    "type": "keepalive",
                    "data": {"timestamp": datetime.now(UTC).isoformat()}
                })
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally for study {study_id}")
    except Exception as e:
        logger.error(f"WebSocket error for study {study_id}: {e}")
    finally:
        await manager.disconnect(websocket, study_id)


# Helper function for broadcasting events (to be called by event subscribers)
async def broadcast_presence_event(study_id: str, event_type: str, event_data: dict):
    """
    Broadcast a presence event to all WebSocket clients for a study.

    This function should be called by event subscribers when presence
    events are published to the event bus.

    Args:
        study_id: Study ID
        event_type: Event type (e.g., "presence.user_joined")
        event_data: Event payload
    """
    message = {
        "type": event_type,
        "data": {
            **event_data,
            "timestamp": datetime.now(UTC).isoformat()
        }
    }
    await manager.broadcast_to_study(study_id, message)
