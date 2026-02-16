# PGN/FEN Import/Export Module

## 📋 Overview

This module provides APIs for importing and exporting chess content in various formats.

## 🎯 Current Features

### ✅ FEN Import
Create Study Chapters from custom starting positions.

**Endpoint**: `POST /api/v1/import-export/fen/import`

**Use Cases**:
- 🏁 Endgame practice (e.g., King+Queen vs King)
- 🧩 Puzzle analysis from specific positions
- 📚 Middlegame training
- 🎲 Chess960 starting positions

**Example**:
```python
# Import a rook endgame position
POST /api/v1/import-export/fen/import
{
    "study_id": "abc123",
    "chapter_title": "Rook Endgame Practice",
    "fen": "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
}

# Response
{
    "chapter_id": "xyz789",
    "starting_fen": "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
    "message": "Chapter created successfully from FEN position"
}
```

## 🔮 Future Features

### ⏸️ PGN Import (Phase 2+)
- Import complete games with variations
- Support for comments and NAGs
- Multi-game import

### ⏸️ PGN Export
- Export chapters to standard PGN format
- Include variations and annotations

## 🏗️ Architecture

```
pgn_fen_import_export/
├── api/
│   ├── endpoints.py      # FastAPI routes
│   └── schemas.py        # Pydantic DTOs
├── services/
│   ├── fen_validator.py  # FEN format validation
│   └── fen_importer.py   # Business logic for FEN import
└── tests/
    ├── test_fen_validator.py
    ├── test_fen_importer.py
    └── test_endpoints.py
```

## 🔗 Dependencies

This module integrates with:
- `workspace` module: Uses `StudyRepository` for chapter creation
- `storage` module: Uploads tree.json to R2
- Frontend `patch/parsing/`: Client-side FEN validation and parsing

## 📚 Documentation

See `fen_import.md` in project root for detailed implementation plan.
