# Workspace System Protocols

> **IMPORTANT**: These protocols form the foundation of the system and should NOT be changed lightly once deployed.

## Overview

This document defines the core protocols, types, and conventions that govern the workspace system. These definitions are considered "frozen" after initial deployment and require careful migration planning for any changes.

## 1. Node Types

The system supports three types of nodes in the workspace tree:

| Type | Description | Characteristics |
|------|-------------|----------------|
| `workspace` | Top-level container | Root of the tree, contains folders and studies |
| `folder` | Organization unit | Can nest infinitely, acts as container |
| `study` | Chess content | Leaf node, contains chapters and variations |

**Key Decision**: Folders support **infinite nesting** for maximum flexibility. While the backend supports this, the UI may limit display depth to ~10 levels for usability.

## 2. Permission Levels

Five-tier permission system from highest to lowest:

| Permission | Abilities | Use Case |
|------------|-----------|----------|
| `owner` | Full control, can delete, transfer ownership | Creator of the object |
| `admin` | Manage members, change settings | Trusted collaborator |
| `editor` | Edit content, add chapters, modify variations | Active contributor |
| `commenter` | Create discussions, reply, react | Discussion participant |
| `viewer` | Read-only access | Observer, student |

**Permission Rules**:
- `viewer` cannot write
- `editor` cannot manage ACL (only `admin`/`owner` can)
- `commenter` can participate in discussions but cannot edit study content
- All permissions inherit read access

## 3. Event Types

The system is **event-driven**. Every write operation produces an event. Events power:
- Real-time WebSocket updates
- Notification creation
- Search index updates
- Activity logging
- Audit trails
- Undo/redo functionality

### Event Categories

**Node Operations**:
- `workspace.created/updated/deleted/moved`
- `folder.created/renamed/deleted/moved`
- `study.created/updated/deleted/moved`
- `layout.updated`

**ACL Operations**:
- `acl.shared/revoked/role_changed`
- `acl.link_created/revoked`
- `acl.inherited/inheritance_broken`

**Study Content**:
- `study.chapter.imported/created/renamed/deleted/reordered`
- `study.move.added/deleted`
- `study.variation.promoted/demoted/reordered`
- `study.move_annotation.added/updated/deleted`
- `study.snapshot.created/rollback`

**Discussion System**:
- `discussion.thread.created/updated/deleted/pinned/resolved`
- `discussion.reply.added/edited/deleted`
- `discussion.reaction.added/removed`
- `discussion.mention`

**Export**:
- `pgn.export.requested/completed/failed`
- `pgn.clipboard.generated`

**Presence**:
- `presence.user_joined/left/idle/active`
- `presence.cursor_moved`

**Notifications**:
- `notification.created/read/dismissed/bulk_read`

**Trash**:
- `node.soft_deleted/restored/permanently_deleted`

## 4. Storage Conventions (R2)

All large objects are stored in Cloudflare R2 with consistent key patterns:

```
r2://workspace-storage/
├── raw/{upload_id}.pgn                 # Original uploads (optional)
├── chapters/{chapter_id}.pgn           # Normalized chapters
├── exports/{job_id}.{pgn|zip}          # Export artifacts
└── snapshots/{study_id}/{version}.json # Version snapshots
```

**Key Rules**:
- IDs must be globally unique
- Keys are immutable once created
- Use presigned URLs for downloads (1 hour expiry)
- Content-Type must be set correctly (`application/x-chess-pgn`, `application/zip`, etc.)

## 5. Study Limits

### 64 Chapter Limit

**Core Architectural Decision**: Each study is limited to **64 chapters** (chess board = 64 squares, memorable).

**Rationale**:
- Prevents single study from becoming unwieldy
- Ensures UI performance
- Provides natural organization boundary

**Auto-Split Behavior**:
When importing PGN with > 64 chapters:
1. System creates a folder (user provides `base_name`)
2. Creates multiple studies: `{base_name}_1`, `{base_name}_2`, ...
3. Each study holds ≤ 64 chapters
4. User receives `ImportReport` with created objects

### Other Limits

- Max variations per move: **10**
- Max annotation length: **10,000 characters**
- Max chapter title: **200 characters**

## 6. Discussion System

### Dual-Layer Comment Model

**Critical Design**: Separate "professional annotations" from "user discussions"

| Feature | Move Annotation | Discussion |
|---------|----------------|-----------|
| **Purpose** | Professional chess analysis | User communication |
| **Storage** | Part of variation tree | Separate `discussions` table |
| **Export** | ✅ Exported with PGN | ❌ Not exported |
| **Permission** | Requires `editor` | Requires `commenter` |
| **Format** | NAG + text | Markdown + rich text |

**Why Separate?**

1. **PGN Purity**: Only professional analysis exports with PGN
2. **Social Flexibility**: Users can discuss without affecting study content
3. **Permission Granularity**: `commenter` role enables discussion-only participation

### Discussion Features

- **Thread Types**: `question`, `suggestion`, `note`
- **Nesting**: Max **5 levels** of reply depth
- **Rich Text**: Markdown, code highlighting, FEN/PGN snippets
- **Interactions**: Reactions (👍 ❤️ 🎯), @mentions, quote replies
- **Resolution**: Questions can be marked as resolved

## 7. Notification System

### Channels

- **IN_APP** (required): Real-time WebSocket + notification center
- **EMAIL** (optional): User-configurable, supports digests
- **PUSH** (future): Browser/mobile push notifications

### Notification Types

- **Collaboration**: Share invites, permission changes
- **Content**: Study updates, new chapters
- **Discussion**: @mentions, replies, resolved questions
- **System**: Export completion, trash cleanup reminders

### User Preferences

Users can configure:
- Which events trigger notifications
- Which channels to use (in-app, email, push)
- Digest frequency (realtime, daily, weekly)
- Quiet hours (do not disturb periods)
- Muted objects (silence specific studies/folders)

## 8. Presence & Collaboration

### Online Status

- **ACTIVE**: Recent activity (< 30s)
- **IDLE**: Inactive 30s - 5min
- **AWAY**: Inactive > 5min

**Heartbeat Mechanism**:
- Clients send heartbeat every 20-30s
- Server updates presence status
- Sessions timeout after 30min

### Cursor Tracking

Users can see:
- Who is viewing the same study
- Which chapter they're on
- Which move they're looking at
- Their activity status (typing, idle, away)

### Conflict Resolution

**Optimistic Locking**:
- Every write includes version/etag
- Conflicts return HTTP 409
- Frontend prompts user to refresh or merge

## 9. Version History

### Snapshot Strategy

**Automatic Snapshots**:
- Critical operations (import, delete chapter, promote variation)
- Periodic (every 10 operations or 5 minutes)
- Manual checkpoints (user-initiated)

**Snapshot Storage**:
- Metadata in DB (version number, timestamp, author, summary)
- Full content in R2 (`snapshots/{study_id}/{version}.json`)

### Rollback

- Creates new version (doesn't delete history)
- Records "rollback to version X"
- Supports selective rollback (single chapter or variation)

## 10. Export System

### Formats

- **PGN**: Single file, all chapters merged
- **ZIP**: Multiple files, one per chapter

### Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `full` | Complete PGN with annotations and variations | Full backup |
| `no_comment` | Variations without annotations | Sharing without analysis |
| `raw` | Main line only, no variations | Clean games |
| `clip` | From specific move (clean before, keep after) | Share position analysis |

### Job System

Large exports run asynchronously:
1. Client requests export → receives `job_id`
2. Server processes export in background
3. Artifact stored in R2
4. Event `pgn.export.completed` fires
5. Client gets presigned download URL

## 11. Implementation Phases

The system is built in **12 phases**:

1. **Phase 0**: Define protocols (this document) ✅
2. **Phase 1**: Node tree + permissions
3. **Phase 2**: Study import + chapter detection
4. **Phase 3**: Variation tree editing
5. **Phase 4**: PGN cleaner
6. **Phase 5**: Discussion system
7. **Phase 6**: Notification system
8. **Phase 7**: Presence & collaboration
9. **Phase 8**: Version history
10. **Phase 9**: Export & packaging
11. **Phase 10**: Search
12. **Phase 11**: Email notifications (optional)
13. **Phase 12**: Activity log & audit

## 12. Testing Requirements

Every phase must achieve:
- ✅ All checklist items completed
- ✅ Test coverage > 80%
- ✅ All tests passing
- ✅ Type checking (mypy) passing
- ✅ Linting (ruff) passing
- ✅ Code formatted (black)

## Conclusion

These protocols form the "constitution" of the workspace system. Changes require:
1. Strong justification
2. Migration plan
3. Backward compatibility strategy
4. Team consensus
5. User communication

When in doubt, **do not change protocols** — adapt the implementation instead.
