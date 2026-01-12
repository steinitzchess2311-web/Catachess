# Layout Events

This document describes the fine-grained layout events used to optimize collaborative editing experience.

## Overview

Layout events track how users arrange nodes (workspaces, folders, studies) in their visual workspace. Fine-grained events allow the frontend to optimize updates and provide smooth collaborative UX.

## Event Types

### 1. `layout.node_moved`

**Purpose**: Single node drag-and-drop position update

**When to emit**: User drags a single node to a new position

**Payload**:
```json
{
  "node_id": "study-abc123",
  "old_position": {"x": 100, "y": 200, "z": 1},
  "new_position": {"x": 150, "y": 250, "z": 1}
}
```

**Frontend Handling**:
- Update only the moved node's position
- Smooth animation from old to new position
- No need to reload entire layout

**Use Case**:
```
User drags "Opening Repertoire" study from left to right side of canvas
→ Emit layout.node_moved
→ Other users see smooth animation of that study moving
```

### 2. `layout.auto_arranged`

**Purpose**: Batch layout update (multiple nodes rearranged)

**When to emit**: Auto-arrange algorithm repositions multiple nodes

**Payload**:
```json
{
  "workspace_id": "workspace-xyz",
  "algorithm": "grid" | "tree" | "force_directed",
  "affected_nodes": [
    {"node_id": "study-1", "position": {"x": 0, "y": 0, "z": 0}},
    {"node_id": "study-2", "position": {"x": 200, "y": 0, "z": 0}},
    {"node_id": "folder-3", "position": {"x": 0, "y": 200, "z": 0}}
  ]
}
```

**Frontend Handling**:
- Reload entire layout from server
- Animate all nodes to new positions
- Show "Arranging..." indicator

**Use Case**:
```
User clicks "Auto-arrange" button
→ Backend calculates optimal layout
→ Emit layout.auto_arranged with all new positions
→ All collaborative users see the new arrangement
```

### 3. `layout.view_changed`

**Purpose**: View mode or zoom level change

**When to emit**: User switches between view modes or changes zoom

**Payload**:
```json
{
  "workspace_id": "workspace-xyz",
  "view_mode": "grid" | "list" | "board",
  "zoom_level": 1.5,
  "user_id": "user-123"
}
```

**Frontend Handling**:
- Update local view settings (per-user)
- Don't force other users to change view
- Optionally sync if user prefers

**Use Case**:
```
User switches from grid view to list view
→ Emit layout.view_changed
→ Other users can see what view User A is using
→ Each user maintains their own view preference
```

### 4. `layout.updated` (Generic)

**Purpose**: Fallback for complex layout changes

**When to emit**: Layout changes that don't fit the above categories

**Payload**:
```json
{
  "workspace_id": "workspace-xyz",
  "change_type": "group_created" | "group_deleted" | "metadata_updated",
  "details": {
    // Flexible payload based on change_type
  }
}
```

**Frontend Handling**:
- Reload affected portion of layout
- Use general refresh strategy

## Event Emission Guidelines

### When to Use Which Event?

```
┌─────────────────────┬──────────────────────┬─────────────────┐
│ User Action         │ Event to Emit        │ Frontend Action │
├─────────────────────┼──────────────────────┼─────────────────┤
│ Drag single node    │ layout.node_moved    │ Update 1 node   │
│ Auto-arrange all    │ layout.auto_arranged │ Reload layout   │
│ Switch view mode    │ layout.view_changed  │ Update view     │
│ Create group        │ layout.updated       │ Refresh groups  │
│ Zoom in/out         │ layout.view_changed  │ Update zoom     │
│ Bulk move (manual)  │ layout.auto_arranged │ Reload layout   │
└─────────────────────┴──────────────────────┴─────────────────┘
```

### Decision Tree

```
Is it a single node position change?
├─ Yes → layout.node_moved
└─ No
   └─ Is it a view/zoom change?
      ├─ Yes → layout.view_changed
      └─ No
         └─ Is it multiple nodes repositioned?
            ├─ Yes → layout.auto_arranged
            └─ No → layout.updated
```

## Implementation Examples

### Backend: Emitting Events

```python
# domain/services/workspace_service.py

async def move_node(
    self,
    node_id: str,
    new_position: Position,
    user_id: str
) -> None:
    """Move a single node to new position."""
    node = await self.node_repo.get_by_id(node_id)
    old_position = node.layout_metadata.get('position')

    # Update position
    node.layout_metadata['position'] = {
        'x': new_position.x,
        'y': new_position.y,
        'z': new_position.z
    }
    await self.node_repo.update(node)

    # Emit fine-grained event
    await self.event_bus.publish(
        event_type=EventType.LAYOUT_NODE_MOVED,
        actor_id=user_id,
        target_id=node_id,
        payload={
            'node_id': node_id,
            'old_position': old_position,
            'new_position': new_position.dict()
        }
    )


async def auto_arrange(
    self,
    workspace_id: str,
    algorithm: str,
    user_id: str
) -> list[Node]:
    """Auto-arrange all nodes in workspace."""
    nodes = await self.node_repo.list_by_workspace(workspace_id)

    # Calculate new positions
    new_positions = self.layout_algorithm.arrange(nodes, algorithm)

    # Update all nodes
    affected = []
    for node, position in zip(nodes, new_positions):
        node.layout_metadata['position'] = position
        await self.node_repo.update(node)
        affected.append({
            'node_id': node.id,
            'position': position
        })

    # Emit batch event
    await self.event_bus.publish(
        event_type=EventType.LAYOUT_AUTO_ARRANGED,
        actor_id=user_id,
        target_id=workspace_id,
        payload={
            'workspace_id': workspace_id,
            'algorithm': algorithm,
            'affected_nodes': affected
        }
    )

    return nodes
```

### Frontend: Handling Events

```typescript
// frontend/services/layoutEventHandler.ts

class LayoutEventHandler {
  constructor(private canvas: LayoutCanvas) {}

  handleEvent(event: LayoutEvent) {
    switch (event.type) {
      case 'layout.node_moved':
        this.handleNodeMoved(event);
        break;

      case 'layout.auto_arranged':
        this.handleAutoArranged(event);
        break;

      case 'layout.view_changed':
        this.handleViewChanged(event);
        break;

      case 'layout.updated':
        this.handleGenericUpdate(event);
        break;
    }
  }

  private handleNodeMoved(event: NodeMovedEvent) {
    const { node_id, old_position, new_position } = event.payload;

    // Animate single node
    this.canvas.animateNode(node_id, {
      from: old_position,
      to: new_position,
      duration: 300,
      easing: 'ease-out'
    });

    // Don't reload entire layout
  }

  private handleAutoArranged(event: AutoArrangedEvent) {
    const { affected_nodes } = event.payload;

    // Show arranging indicator
    this.canvas.showOverlay('Arranging layout...');

    // Animate all affected nodes
    const animations = affected_nodes.map(node =>
      this.canvas.animateNode(node.node_id, {
        to: node.position,
        duration: 500,
        easing: 'ease-in-out'
      })
    );

    // Wait for animations to complete
    Promise.all(animations).then(() => {
      this.canvas.hideOverlay();
    });
  }

  private handleViewChanged(event: ViewChangedEvent) {
    const { view_mode, zoom_level, user_id } = event.payload;

    if (user_id === this.currentUserId) {
      // This is our own view change, already applied
      return;
    }

    // Show other user's view indicator (optional)
    this.canvas.showUserViewIndicator(user_id, {
      mode: view_mode,
      zoom: zoom_level
    });

    // Don't force change our own view
  }
}
```

## Performance Optimization

### Batching Updates

```typescript
// Batch multiple rapid position updates
class LayoutUpdateBatcher {
  private pending: Map<string, Position> = new Map();
  private timer: number | null = null;

  scheduleUpdate(nodeId: string, position: Position) {
    this.pending.set(nodeId, position);

    if (this.timer) {
      clearTimeout(this.timer);
    }

    this.timer = setTimeout(() => this.flush(), 100);
  }

  private flush() {
    if (this.pending.size === 1) {
      // Single update → use layout.node_moved
      const [nodeId, position] = this.pending.entries().next().value;
      this.emitNodeMoved(nodeId, position);
    } else if (this.pending.size > 1) {
      // Multiple updates → use layout.auto_arranged
      this.emitAutoArranged(this.pending);
    }

    this.pending.clear();
    this.timer = null;
  }
}
```

### Throttling Events

```python
# backend: Throttle layout events per user
class LayoutEventThrottler:
    def __init__(self, window: float = 1.0):
        self.window = window
        self.last_emit: dict[str, float] = {}

    async def should_emit(self, user_id: str) -> bool:
        now = time.time()
        last = self.last_emit.get(user_id, 0)

        if now - last >= self.window:
            self.last_emit[user_id] = now
            return True

        return False
```

## Testing

```python
# tests/test_layout_events.py

async def test_node_moved_event():
    """Test that moving a node emits correct event."""
    # Move node
    await service.move_node(
        node_id="study-123",
        new_position=Position(x=100, y=200, z=0),
        user_id="user-1"
    )

    # Verify event
    events = await event_repo.list_by_type(EventType.LAYOUT_NODE_MOVED)
    assert len(events) == 1
    assert events[0].payload['node_id'] == "study-123"
    assert events[0].payload['new_position'] == {'x': 100, 'y': 200, 'z': 0}


async def test_auto_arrange_event():
    """Test that auto-arrange emits batch event."""
    # Auto-arrange
    await service.auto_arrange(
        workspace_id="ws-1",
        algorithm="grid",
        user_id="user-1"
    )

    # Verify event
    events = await event_repo.list_by_type(EventType.LAYOUT_AUTO_ARRANGED)
    assert len(events) == 1
    assert events[0].payload['algorithm'] == "grid"
    assert len(events[0].payload['affected_nodes']) > 1
```

## Best Practices

1. **Use specific events**: Prefer `layout.node_moved` over generic `layout.updated`
2. **Batch when possible**: Multiple moves → `layout.auto_arranged`
3. **Throttle events**: Limit layout events to prevent spam
4. **Optimize frontend**: Only update affected nodes
5. **Test collaboration**: Verify multi-user scenarios

## Migration from Generic Events

If currently using only `layout.updated`:

1. Add new event types to `events/types.py` ✅
2. Update services to emit specific events
3. Keep `layout.updated` for backwards compatibility
4. Update frontend to handle both old and new events
5. Deprecate `layout.updated` after migration

## Related Documentation

- [Event System](./event_system.md)
- [Collaboration](./collaboration.md)
- [WebSocket Protocol](./websocket_protocol.md)
