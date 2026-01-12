"""
Integration tests for presence WebSocket functionality.

Tests WebSocket connections, message broadcasting, and event handling.
"""

import pytest
import asyncio
from datetime import datetime, UTC

from workspace.api.websocket.presence_ws import (
    ConnectionManager,
    broadcast_presence_event
)


@pytest.mark.asyncio
class TestPresenceWebSocket:
    """Tests for presence WebSocket functionality."""

    async def test_connection_manager_accepts_connection(self):
        """Test ConnectionManager accepts new connections."""
        manager = ConnectionManager()

        # Mock WebSocket
        class MockWebSocket:
            def __init__(self):
                self.accepted = False
                self.messages = []
                self.client_state = "CONNECTED"

            async def accept(self):
                self.accepted = True

            async def send_json(self, data):
                self.messages.append(data)

        ws = MockWebSocket()
        await manager.connect(ws, "study1")

        assert ws.accepted
        assert "study1" in manager.active_connections
        assert ws in manager.active_connections["study1"]

    async def test_connection_manager_disconnects(self):
        """Test ConnectionManager removes disconnected connections."""
        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        ws = MockWebSocket()
        await manager.connect(ws, "study1")

        assert "study1" in manager.active_connections
        assert ws in manager.active_connections["study1"]

        await manager.disconnect(ws, "study1")

        # Connection should be removed
        assert "study1" not in manager.active_connections

    async def test_connection_manager_broadcasts_to_study(self):
        """Test broadcasting messages to all connections in a study."""
        manager = ConnectionManager()

        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                self.messages.append(data)

        # Connect multiple clients to same study
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1, "study1")
        await manager.connect(ws2, "study1")

        # Broadcast message
        message = {
            "type": "presence.user_joined",
            "data": {"user_id": "user1", "study_id": "study1"}
        }
        await manager.broadcast_to_study("study1", message)

        # Both clients should receive message
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 1
        assert ws1.messages[0] == message
        assert ws2.messages[0] == message

    async def test_connection_manager_isolates_studies(self):
        """Test that broadcasts are isolated per study."""
        manager = ConnectionManager()

        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                self.messages.append(data)

        # Connect clients to different studies
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        await manager.connect(ws1, "study1")
        await manager.connect(ws2, "study2")

        # Broadcast to study1
        message = {
            "type": "presence.user_joined",
            "data": {"user_id": "user1", "study_id": "study1"}
        }
        await manager.broadcast_to_study("study1", message)

        # Only study1 client should receive message
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 0

    async def test_connection_manager_handles_failed_sends(self):
        """Test handling of failed message sends."""
        manager = ConnectionManager()

        class FailingWebSocket:
            def __init__(self):
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                raise Exception("Connection lost")

        class WorkingWebSocket:
            def __init__(self):
                self.messages = []
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                self.messages.append(data)

        # Connect both working and failing websockets
        failing_ws = FailingWebSocket()
        working_ws = WorkingWebSocket()
        await manager.connect(failing_ws, "study1")
        await manager.connect(working_ws, "study1")

        # Broadcast message
        message = {"type": "test", "data": {}}
        await manager.broadcast_to_study("study1", message)

        # Working connection should receive message
        assert len(working_ws.messages) == 1
        # Failing connection should be removed
        assert failing_ws not in manager.active_connections["study1"]

    async def test_broadcast_presence_event_helper(self):
        """Test the broadcast_presence_event helper function."""
        # This is a basic test since the function uses the global manager
        # In production, you'd want proper dependency injection

        event_data = {
            "user_id": "user1",
            "session_id": "session1",
            "status": "active",
            "chapter_id": "chapter1"
        }

        # Should not raise exception even with no connections
        await broadcast_presence_event(
            study_id="study1",
            event_type="presence.user_joined",
            event_data=event_data
        )

    async def test_multiple_connections_same_study(self):
        """Test multiple WebSocket connections to same study."""
        manager = ConnectionManager()

        class MockWebSocket:
            def __init__(self, name):
                self.name = name
                self.messages = []
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                self.messages.append(data)

        # Connect 5 clients to same study
        clients = [MockWebSocket(f"client{i}") for i in range(5)]
        for client in clients:
            await manager.connect(client, "study1")

        # Broadcast message
        message = {"type": "test", "data": {"value": 123}}
        await manager.broadcast_to_study("study1", message)

        # All clients should receive message
        for client in clients:
            assert len(client.messages) == 1
            assert client.messages[0] == message

    async def test_disconnect_cleans_up_empty_study(self):
        """Test that disconnecting last client removes study from manager."""
        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        ws = MockWebSocket()
        await manager.connect(ws, "study1")
        assert "study1" in manager.active_connections

        await manager.disconnect(ws, "study1")
        # Study should be removed when last client disconnects
        assert "study1" not in manager.active_connections

    async def test_connection_manager_concurrent_operations(self):
        """Test concurrent connection/disconnection operations."""
        manager = ConnectionManager()

        class MockWebSocket:
            def __init__(self, id):
                self.id = id
                self.client_state = "CONNECTED"

            async def accept(self):
                pass

            async def send_json(self, data):
                pass

        # Simulate concurrent connections
        async def connect_client(id):
            ws = MockWebSocket(id)
            await manager.connect(ws, "study1")
            await asyncio.sleep(0.01)  # Small delay
            return ws

        # Connect multiple clients concurrently
        websockets = await asyncio.gather(*[
            connect_client(i) for i in range(10)
        ])

        # Should have 10 connections
        assert len(manager.active_connections["study1"]) == 10

        # Disconnect some concurrently
        async def disconnect_client(ws):
            await asyncio.sleep(0.01)
            await manager.disconnect(ws, "study1")

        await asyncio.gather(*[
            disconnect_client(ws) for ws in websockets[:5]
        ])

        # Should have 5 connections remaining
        assert len(manager.active_connections["study1"]) == 5
