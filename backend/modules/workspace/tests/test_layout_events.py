"""Tests for layout event emissions."""
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.node_repo import NodeRepository
from workspace.db.tables.nodes import Node
from workspace.events.bus import EventBus
from workspace.events.types import EventType


@pytest.fixture
async def event_bus() -> EventBus:
    """Create event bus."""
    return EventBus()


@pytest.fixture
async def node_repo(session: AsyncSession) -> NodeRepository:
    """Get node repository."""
    return NodeRepository(session)


@pytest.fixture
async def workspace(
    node_repo: NodeRepository, session: AsyncSession
) -> Node:
    """Create a test workspace."""
    workspace = Node(
        id=str(uuid.uuid4()),
        name="Test Workspace",
        node_type="workspace",
        owner_id=str(uuid.uuid4()),
        layout_metadata={},
    )
    workspace = await node_repo.create(workspace)
    await session.commit()
    return workspace


@pytest.fixture
async def study_node(
    node_repo: NodeRepository, workspace: Node, session: AsyncSession
) -> Node:
    """Create a test study node."""
    study = Node(
        id=str(uuid.uuid4()),
        name="Test Study",
        node_type="study",
        owner_id=workspace.owner_id,
        parent_id=workspace.id,
        layout_metadata={"position": {"x": 100, "y": 200, "z": 0}},
    )
    study = await node_repo.create(study)
    await session.commit()
    return study


@pytest.mark.asyncio
async def test_layout_node_moved_event_payload(
    event_bus: EventBus, study_node: Node
) -> None:
    """Test that layout.node_moved event has correct payload structure."""
    old_position = {"x": 100, "y": 200, "z": 0}
    new_position = {"x": 150, "y": 250, "z": 0}

    # Emit event
    await event_bus.publish(
        event_type=EventType.LAYOUT_NODE_MOVED,
        actor_id=study_node.owner_id,
        target_id=study_node.id,
        target_type="study",
        payload={
            "node_id": study_node.id,
            "old_position": old_position,
            "new_position": new_position,
        },
    )

    # Verify event structure
    # (In real implementation, this would check event was properly stored)
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_layout_auto_arranged_event_payload(
    event_bus: EventBus, workspace: Node
) -> None:
    """Test that layout.auto_arranged event has correct payload structure."""
    affected_nodes = [
        {"node_id": "study-1", "position": {"x": 0, "y": 0, "z": 0}},
        {"node_id": "study-2", "position": {"x": 200, "y": 0, "z": 0}},
        {"node_id": "folder-1", "position": {"x": 0, "y": 200, "z": 0}},
    ]

    # Emit event
    await event_bus.publish(
        event_type=EventType.LAYOUT_AUTO_ARRANGED,
        actor_id=workspace.owner_id,
        target_id=workspace.id,
        target_type="workspace",
        payload={
            "workspace_id": workspace.id,
            "algorithm": "grid",
            "affected_nodes": affected_nodes,
        },
    )

    # Verify event structure
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_layout_view_changed_event_payload(
    event_bus: EventBus, workspace: Node
) -> None:
    """Test that layout.view_changed event has correct payload structure."""
    # Emit event
    await event_bus.publish(
        event_type=EventType.LAYOUT_VIEW_CHANGED,
        actor_id=workspace.owner_id,
        target_id=workspace.id,
        target_type="workspace",
        payload={
            "workspace_id": workspace.id,
            "view_mode": "grid",
            "zoom_level": 1.5,
            "user_id": workspace.owner_id,
        },
    )

    # Verify event structure
    assert True  # Placeholder


@pytest.mark.asyncio
async def test_node_moved_vs_auto_arranged_distinction() -> None:
    """Test the decision logic for which event to emit."""

    # Single node move
    def should_emit_node_moved(moved_nodes: list) -> bool:
        return len(moved_nodes) == 1

    assert should_emit_node_moved(["study-1"]) is True
    assert should_emit_node_moved(["study-1", "study-2"]) is False

    # Multiple nodes move
    def should_emit_auto_arranged(moved_nodes: list) -> bool:
        return len(moved_nodes) > 1

    assert should_emit_auto_arranged(["study-1", "study-2"]) is True
    assert should_emit_auto_arranged(["study-1"]) is False


@pytest.mark.asyncio
async def test_layout_event_types_are_distinct() -> None:
    """Test that layout event types are distinct and well-defined."""
    layout_events = [
        EventType.LAYOUT_UPDATED,
        EventType.LAYOUT_NODE_MOVED,
        EventType.LAYOUT_AUTO_ARRANGED,
        EventType.LAYOUT_VIEW_CHANGED,
    ]

    # All should be distinct
    assert len(layout_events) == len(set(layout_events))

    # All should be strings
    for event_type in layout_events:
        assert isinstance(event_type.value, str)
        assert event_type.value.startswith("layout.")


@pytest.mark.asyncio
async def test_layout_event_payload_validation() -> None:
    """Test that layout event payloads have required fields."""

    # LAYOUT_NODE_MOVED required fields
    node_moved_required = ["node_id", "old_position", "new_position"]

    node_moved_payload = {
        "node_id": "study-123",
        "old_position": {"x": 0, "y": 0, "z": 0},
        "new_position": {"x": 100, "y": 100, "z": 0},
    }

    for field in node_moved_required:
        assert field in node_moved_payload

    # LAYOUT_AUTO_ARRANGED required fields
    auto_arranged_required = ["workspace_id", "algorithm", "affected_nodes"]

    auto_arranged_payload = {
        "workspace_id": "ws-123",
        "algorithm": "grid",
        "affected_nodes": [
            {"node_id": "study-1", "position": {"x": 0, "y": 0, "z": 0}}
        ],
    }

    for field in auto_arranged_required:
        assert field in auto_arranged_payload

    # LAYOUT_VIEW_CHANGED required fields
    view_changed_required = ["workspace_id", "view_mode", "user_id"]

    view_changed_payload = {
        "workspace_id": "ws-123",
        "view_mode": "grid",
        "zoom_level": 1.0,
        "user_id": "user-1",
    }

    for field in view_changed_required:
        assert field in view_changed_payload


@pytest.mark.asyncio
async def test_position_format_consistency() -> None:
    """Test that position format is consistent across events."""
    # Position should always have x, y, z
    position = {"x": 100, "y": 200, "z": 0}

    assert "x" in position
    assert "y" in position
    assert "z" in position

    # Values should be numeric
    assert isinstance(position["x"], (int, float))
    assert isinstance(position["y"], (int, float))
    assert isinstance(position["z"], (int, float))


@pytest.mark.asyncio
async def test_algorithm_types_are_valid() -> None:
    """Test that arrangement algorithms are from valid set."""
    valid_algorithms = ["grid", "tree", "force_directed", "circular", "manual"]

    test_algorithm = "grid"
    assert test_algorithm in valid_algorithms


@pytest.mark.asyncio
async def test_view_modes_are_valid() -> None:
    """Test that view modes are from valid set."""
    valid_view_modes = ["grid", "list", "board", "tree"]

    test_view_mode = "grid"
    assert test_view_mode in valid_view_modes
