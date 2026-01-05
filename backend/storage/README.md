# Storage Module - Architecture Documentation

**Version**: 1.0 (Frozen)
**Last Updated**: 2026-01-05
**Status**: Production Ready

## Overview

This module provides industrial-grade object storage for Catachess using Cloudflare R2.
It is designed to be maintainable for **2+ years** without architectural changes.

## Design Principles

### 1. Separation of Concerns

The storage system is split into three independent layers:

1. **Infrastructure** (`storage/core`): R2 client, configuration, errors
2. **Content** (`storage/game_history`): What to store (PGN, analysis)
3. **Index** (`storage/game_history/index.py`): Who can see what (Protocol only)

### 2. Business Logic Isolation

The storage layer knows NOTHING about:
- ❌ User authentication
- ❌ Permissions/authorization
- ❌ Database models
- ❌ API endpoints
- ❌ Business rules

It ONLY knows about:
- ✅ R2 operations (put/get/delete)
- ✅ Content format (PGN, JSON)
- ✅ Key patterns

### 3. Single Responsibility

Each module has ONE clear purpose:

| Module | Responsibility | NOT Responsible For |
|--------|---------------|---------------------|
| `core/config.py` | R2 connection settings | What data is stored |
| `core/client.py` | R2 operations (put/get/delete) | Business logic |
| `core/errors.py` | Storage error boundaries | HTTP errors |
| `game_history/keys.py` | Key generation | Content validation |
| `game_history/store.py` | Content storage | Permissions |
| `game_history/index.py` | Index protocol | Implementation |

## Directory Structure

```
backend/storage/
├── __init__.py                 # Package exports
├── README.md                   # This file
│
├── core/                       # Infrastructure Layer
│   ├── __init__.py
│   ├── config.py              # R2 endpoint, bucket, credentials
│   ├── client.py              # Pure R2 client (boto3 wrapper)
│   └── errors.py              # StorageError, ObjectNotFound, etc.
│
└── game_history/              # Content Domain
    ├── __init__.py
    ├── keys.py                # Centralized key generation
    ├── store.py               # PGN/analysis storage operations
    ├── types.py               # GameMeta, DTOs
    └── index.py               # Protocol (interface only, no implementation)
```

## Core Layer (`storage/core`)

### Purpose
Provide a clean, business-agnostic interface to Cloudflare R2.

### Key Files

#### `config.py`
Manages R2 connection configuration.

```python
from storage.core.config import StorageConfig

# Production: Read from environment
config = StorageConfig.from_env()

# Testing: Use test config
config = StorageConfig.for_testing()
```

**Environment Variables Required**:
```bash
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_BUCKET=catachess-data
R2_ACCESS_KEY_ID=<your-access-key>
R2_SECRET_ACCESS_KEY=<your-secret-key>
```

#### `client.py`
The ONLY file that uses boto3.

```python
from storage.core import StorageClient, StorageConfig

config = StorageConfig.from_env()
client = StorageClient(config)

# Store bytes
client.put_object("test.txt", b"hello world")

# Retrieve bytes
content = client.get_object("test.txt")

# Check existence
exists = client.exists("test.txt")

# Delete
client.delete_object("test.txt")
```

**Key Methods**:
- `put_object(key, content, content_type=None)`
- `get_object(key) -> bytes`
- `delete_object(key)`
- `exists(key) -> bool`

#### `errors.py`
Custom exception hierarchy for storage operations.

```python
from storage.core.errors import ObjectNotFound, StorageUnavailable

try:
    content = client.get_object("nonexistent.txt")
except ObjectNotFound:
    print("File doesn't exist")
except StorageUnavailable:
    print("R2 is down, try again later")
```

**Exception Hierarchy**:
- `StorageError` (base)
  - `StorageUnavailable` (transient)
  - `ObjectNotFound` (expected)
  - `ObjectAlreadyExists` (conflict)
  - `InvalidObjectKey` (programmer error)
  - `StoragePermissionDenied` (config error)

## Game History Layer (`storage/game_history`)

### Purpose
Manage game content (PGN files, analysis JSON) without knowing about users or permissions.

### Key Files

#### `keys.py` - THE MOST CRITICAL FILE

This file defines ALL R2 key patterns. **No other file should ever construct a key string.**

```python
from storage.game_history.keys import game_pgn, game_analysis

# Generate keys
pgn_key = game_pgn("8f2a9c")  # "games/8f2a9c.pgn"
analysis_key = game_analysis("8f2a9c")  # "analysis/8f2a9c.json"
```

**Why this matters**:
Keys are the "schema" of object storage. If different parts of the system generate keys differently:
- ❌ You'll lose objects
- ❌ You'll have duplicates
- ❌ You can't migrate
- ❌ Debugging becomes impossible

**Current Key Patterns**:
```
games/{game_id}.pgn          # PGN content
analysis/{game_id}.json      # Engine analysis
training/{game_id}.json      # Training data (future)
thumbnails/{game_id}.png     # Board snapshots (future)
```

#### `store.py` - Content Operations

Store and retrieve game content.

```python
from storage.game_history import save_pgn, load_pgn, save_analysis, load_analysis

# Save PGN
pgn = "[Event \"Test\"]\n[Site \"Chess.com\"]\n\n1. e4 e5"
save_pgn("game_8f2a9c", pgn)

# Load PGN
pgn = load_pgn("game_8f2a9c")

# Save analysis
analysis = {"moves": [...], "blunders": [...]}
save_analysis("game_8f2a9c", analysis)

# Load analysis
analysis = load_analysis("game_8f2a9c")
```

**What it does**:
- ✅ Serialize/deserialize content
- ✅ Handle R2 storage
- ✅ Provide convenience methods

**What it does NOT do**:
- ❌ Check permissions
- ❌ Validate ownership
- ❌ Update database
- ❌ Send notifications

#### `types.py` - Data Transfer Objects

Pure data structures for the storage domain.

```python
from storage.game_history.types import GameMeta

meta: GameMeta = {
    "game_id": "8f2a9c",
    "created_at": datetime.now(),
    "white_player": "player1",
    "black_player": "player2",
    "result": "1-0",
    "event": "Casual Game",
}
```

**These are NOT**:
- ❌ ORM models (those are in `models/`)
- ❌ API schemas (those are in `routers/`)
- ❌ Database tables

**These ARE**:
- ✅ Storage domain DTOs
- ✅ Type hints for IDE support
- ✅ Data containers

#### `index.py` - Protocol (Interface Only)

Defines WHAT an index must do, not HOW to do it.

```python
from storage.game_history.index import GameHistoryIndex

# This is a Protocol (interface), not a class
# You can't instantiate it: GameHistoryIndex()  # Error!

# Future implementations will satisfy this protocol:
# class PostgresGameIndex:
#     def add_game(...): ...
#     def list_games(...): ...
```

**Why Protocol instead of implementation**:
1. **Flexibility**: Can implement with Postgres, R2 JSON, Redis, or anything
2. **Testing**: Easy to create mock indexes
3. **Separation**: Index logic separate from storage logic
4. **Future-proof**: Can change implementation without touching storage

**Methods defined**:
- `add_game(user_id, game_id, ...)`
- `list_games(user_id, limit, offset) -> List[GameMeta]`
- `get_game(user_id, game_id) -> GameMeta | None`
- `remove_game(user_id, game_id)`
- `game_exists_for_user(user_id, game_id) -> bool`

## How It All Fits Together

### Data Flow Example: Storing a Game

```
1. User plays a game
   ↓
2. Service layer creates PGN string
   ↓
3. service calls: save_pgn(game_id, pgn)
   ↓
4. store.py calls: client.put_object(key, bytes)
   ↓
5. R2 stores: games/8f2a9c.pgn
```

### Data Flow Example: Listing User's Games

```
1. User requests "my games"
   ↓
2. Router validates JWT → user_id
   ↓
3. Service calls: index.list_games(user_id)
   ↓
4. Index returns: [GameMeta, GameMeta, ...]
   ↓
5. For each game: content = load_pgn(game_id)
   ↓
6. Router returns list to frontend
```

### Key Insight: Separation of Visibility and Content

```
┌─────────────────────────────────────────┐
│ R2 Storage (Content Pool)              │
│ ┌─────────────────────────────────────┐ │
│ │ games/8f2a9c.pgn                    │ │
│ │ games/71caa2.pgn                    │ │
│ │ analysis/8f2a9c.json                │ │
│ └─────────────────────────────────────┘ │
│  No user info, no permissions          │
└─────────────────────────────────────────┘
                 ↑
                 │ Content
                 │
┌────────────────┴────────────────────────┐
│ Index (Who can see what)                │
│ ┌─────────────────────────────────────┐ │
│ │ user_123 → [8f2a9c, 71caa2]         │ │
│ │ user_456 → [71caa2]                 │ │
│ └─────────────────────────────────────┘ │
│  Tracks visibility, not content        │
└─────────────────────────────────────────┘
```

## Usage Patterns

### Pattern 1: Store a Game

```python
from storage.game_history import save_pgn

# After a game completes
game_id = "game_8f2a9c"
pgn_content = generate_pgn_from_moves(...)

# Store the content
save_pgn(game_id, pgn_content)

# Update the index (future, when implemented)
# index.add_game(user_id, game_id, created_at)
```

### Pattern 2: Retrieve a Game

```python
from storage.game_history import load_pgn
from storage.core.errors import ObjectNotFound

try:
    pgn = load_pgn(game_id)
    return {"pgn": pgn}
except ObjectNotFound:
    return {"error": "Game not found"}, 404
```

### Pattern 3: List User's Games (Future)

```python
# This will work once index is implemented
from storage.game_history import GameHistoryIndex

def list_user_games(user_id: str, index: GameHistoryIndex):
    # Get metadata from index
    games = index.list_games(user_id, limit=20)

    # Load content for each game
    for game in games:
        game["pgn"] = load_pgn(game["game_id"])

    return games
```

## Testing

### Unit Tests (Future)

```python
from storage.core import StorageClient, StorageConfig

def test_storage_client():
    # Use test config
    config = StorageConfig.for_testing()
    client = StorageClient(config)

    # Test operations
    client.put_object("test.txt", b"hello")
    assert client.exists("test.txt")
    content = client.get_object("test.txt")
    assert content == b"hello"
```

### Integration Tests (Future)

```python
from storage.game_history import save_pgn, load_pgn

def test_pgn_storage():
    game_id = "test_game"
    pgn = "[Event \"Test\"]\n\n1. e4 e5"

    save_pgn(game_id, pgn)
    loaded_pgn = load_pgn(game_id)

    assert loaded_pgn == pgn
```

## Migration Guide (If Needed)

### Switching from R2 to S3

1. Update `storage/core/config.py`:
   ```python
   endpoint = "https://s3.amazonaws.com"
   ```

2. No other changes needed! The rest of the system doesn't know about R2.

### Adding a New Content Type

1. Add key function to `storage/game_history/keys.py`:
   ```python
   def game_review(game_id: str) -> str:
       return f"reviews/{game_id}.json"
   ```

2. Add store functions to `storage/game_history/store.py`:
   ```python
   def save_review(game_id: str, review: dict):
       ...
   ```

3. That's it! No changes to core layer needed.

## Security Considerations

### Credentials
- ✅ Stored in environment variables
- ✅ Never committed to git
- ✅ Masked in logs (`config.__repr__`)
- ❌ Never sent to frontend

### Access Control
- ✅ Index layer handles "who can see what"
- ✅ Storage layer is permission-agnostic
- ✅ No public bucket access

### Data Validation
- ✅ Key validation in `client._validate_key()`
- ⚠️ Content validation is service layer responsibility
- ⚠️ PGN parsing happens outside storage

## Performance Considerations

### Caching (Future)
```python
# If needed, add caching in store.py
@lru_cache(maxsize=1000)
def load_pgn(game_id: str) -> str:
    ...
```

### Batch Operations (Future)
```python
# If needed, add bulk operations
def load_pgns_bulk(game_ids: List[str]) -> Dict[str, str]:
    ...
```

## Common Pitfalls to Avoid

### ❌ DON'T: Generate keys outside keys.py
```python
# BAD
key = f"games/{game_id}.pgn"  # Don't do this!

# GOOD
from storage.game_history.keys import game_pgn
key = game_pgn(game_id)
```

### ❌ DON'T: Add business logic to storage
```python
# BAD
def save_pgn(game_id, pgn, user_id):
    if not user_is_teacher(user_id):  # Don't do this!
        raise PermissionError()
    ...

# GOOD
def save_pgn(game_id, pgn):
    # Just store it, permissions checked elsewhere
    ...
```

### ❌ DON'T: Use boto3 directly
```python
# BAD
import boto3
s3 = boto3.client("s3")  # Don't do this!

# GOOD
from storage.core import StorageClient
client = StorageClient(config)
```

## Future Enhancements

When needed (not now):

1. **Implement Index**: Choose Postgres, Redis, or R2 JSON
2. **Add Caching**: LRU cache for frequently accessed games
3. **Add Compression**: gzip PGN files before storage
4. **Add Metadata**: Store game metadata in R2 object metadata
5. **Add Versioning**: Keep history of game edits
6. **Add Encryption**: Client-side encryption for sensitive data

## Questions?

This storage system is designed to be:
- ✅ Easy to understand
- ✅ Easy to test
- ✅ Easy to change
- ✅ Hard to break

If something is unclear, it's a documentation bug. Please ask!

## Version History

- **v1.0** (2026-01-05): Initial implementation with frozen architecture
