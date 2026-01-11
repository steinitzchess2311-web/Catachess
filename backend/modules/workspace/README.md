# Workspace Module

> **Status**: Phase 0 Complete ✅

A comprehensive workspace management system for chess studies, supporting:
- Hierarchical organization (workspace → folders → studies)
- Real-time collaboration with presence tracking
- Rich discussion system separate from chess annotations
- Version history and rollback
- PGN import/export with smart chunking
- Full-text search across content

## Design Documents

- **[Complete Design](claude_plan.md)**: Full architectural specification
- **[Implementation Plan](implement.md)**: 12-phase development roadmap
- **[Protocols](docs/protocols.md)**: Core types and conventions (frozen)

## Architecture Principles

### 1. Backend as Source of Truth

- All business logic in backend
- Frontend is pure rendering layer
- Backend validates all operations

### 2. Large Objects in R2

- PGN files stored in Cloudflare R2
- Database stores only metadata + references
- Presigned URLs for downloads

### 3. Event-Driven Architecture

- Every write operation produces an event
- Events drive real-time updates, notifications, indexing
- Events enable undo/redo and audit trails

### 4. Dual-Layer Comment Model

**Critical Innovation**: Separate professional annotations from user discussions

| Feature | Move Annotation | Discussion |
|---------|----------------|-----------|
| Purpose | Professional analysis | User communication |
| Exported | ✅ Yes (with PGN) | ❌ No |
| Permission | `editor` | `commenter` |

## Key Features

### Study Management

- **Smart Import**: Auto-detect chapters, split at 64-chapter limit
- **PGN Cleaner**: Copy from any position (remove before, keep after)
- **Export Modes**: Full, no-comments, mainline-only, or clip from move

### Collaboration

- **Real-time Presence**: See who's online and where they're looking
- **Optimistic Locking**: Conflict detection with version/etag
- **Cursor Tracking**: Know where collaborators are in the study

### Version Control

- **Auto-snapshots**: Critical operations + periodic saves
- **Version Compare**: Visual diff between versions
- **Selective Rollback**: Revert single chapter or whole study

### Permissions

Five-tier system: `owner` > `admin` > `editor` > `commenter` > `viewer`

- Granular control at workspace/folder/study level
- Inheritable or independent permissions
- Share links with optional password/expiry

## Development Status

### Phase 0: Protocols (Complete ✅)

- ✅ Core types defined (`NodeType`, `Permission`, etc.)
- ✅ Event taxonomy complete (~60 event types)
- ✅ R2 key conventions established
- ✅ Study limits defined (64 chapters, auto-split)
- ✅ Protocol documentation written

### Phase 1: Node Tree + Permissions (Next)

- [ ] Database tables: `nodes`, `acl`, `events`
- [ ] Domain services: node operations, sharing
- [ ] API endpoints: workspace/folder CRUD
- [ ] WebSocket: event subscriptions
- [ ] Tests: tree operations, permissions, events

## Project Structure

```
workspace/
├── api/              # API layer (FastAPI)
│   ├── schemas/      # Pydantic models
│   ├── endpoints/    # REST endpoints
│   └── websocket/    # WebSocket handlers
├── domain/           # Business logic
│   ├── models/       # Domain models
│   ├── services/     # Domain services
│   └── policies/     # Business rules
├── pgn/              # PGN processing
│   ├── parser/       # Parse & normalize
│   ├── cleaner/      # Clean & clip PGN
│   └── serializer/   # Tree ↔ PGN
├── storage/          # R2 client
├── db/               # Database layer
│   ├── tables/       # ORM models
│   └── repos/        # Repositories
├── events/           # Event system
│   └── subscribers/  # Event handlers
├── collaboration/    # Real-time features
├── notifications/    # Notification system
├── jobs/             # Async jobs
└── tests/            # Test suite
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (for Celery)
- Cloudflare R2 or S3-compatible storage

### Installation

```bash
cd backend/modules/workspace
pip install -e ".[dev]"
```

### Configuration

Create `.env` file:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/catachess
REDIS_URL=redis://localhost:6379/0
R2_ENDPOINT=https://xxx.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=catachess-workspace
```

### Running Tests

```bash
pytest -v --cov=workspace --cov-report=term-missing
```

### Code Quality

```bash
# Type checking
mypy workspace

# Linting
ruff check workspace

# Formatting
black workspace
```

## Implementation Roadmap

The system is built in 12 phases (see [implement.md](implement.md) for details):

1. **Phase 0**: Define protocols ✅
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

**Estimated Timeline**: 50-60 working days (2-3 months)

## Testing Strategy

Five layers of testing:

1. **Unit Tests**: Individual functions and classes
2. **Integration Tests**: Database, storage, events
3. **API Tests**: REST endpoint contracts
4. **Event Tests**: Event production and delivery
5. **Collaboration Tests**: Concurrency and conflicts

**Target Coverage**: > 80% across all layers

## Key Design Decisions

### Why 64 Chapters?

- Memorable (chess board = 64 squares)
- Prevents UI performance issues
- Forces good organization
- Auto-splits large imports cleanly

### Why Separate Annotations from Discussions?

- **PGN purity**: Only professional analysis exports
- **Social flexibility**: Discuss without affecting content
- **Permission granularity**: `commenter` role for discussions only

### Why Event-Driven?

- **Real-time**: WebSocket updates automatic
- **Decoupled**: Add features (notifications, search) without touching core
- **Auditable**: Complete operation history
- **Undoable**: Event stream enables undo/redo

## Contributing

### Development Workflow

1. Pick a Phase from [implement.md](implement.md)
2. Follow the checklist
3. Write tests first (TDD)
4. Implement feature
5. Ensure all tests pass
6. Run type checking and linting
7. Update checklist
8. Commit and push

### Commit Conventions

```
feat: add node tree CRUD operations
fix: correct ACL inheritance logic
test: add variation promote tests
docs: update protocol documentation
```

## License

See main project LICENSE

## Contact

See main project README for contact information
