# Catachess API Documentation

> **Last Updated**: 2025-02-19
>
> **Base URL**: `https://api.catachess.com` (Production)
>
> **Base URL**: `http://localhost:8000` (Development)

新增的端点：
GET /api/v1/workspace/public/studies               
                                                     
  无需鉴权。                                         
                                                     
  Query 参数                                         
                                                     
  ┌────────┬──────┬────────┬───────┬──────────┐      
  │  参数  │ 类型 │ 默认值 │ 范围  │   说明   │      
  ├────────┼──────┼────────┼───────┼──────────┤      
  │ limit  │ int  │ 20     │ 1–100 │ 每页条数 │
  ├────────┼──────┼────────┼───────┼──────────┤
  │ offset │ int  │ 0      │ ≥0    │ 分页偏移 │
  └────────┴──────┴────────┴───────┴──────────┘

  Response 示例

  {
    "items": [
      {
        "id": "abc123",
        "title": "Philidor Defense",
        "owner_id": "user-uuid",
        "created_at": "2026-02-19T10:00:00",
        "updated_at": "2026-02-19T12:00:00"
      }
    ],
    "limit": 20,
    "offset": 0
  }

  排序：按 created_at 降序（最新的在前）。

  分页示例
  GET
  /api/v1/workspace/public/studies?limit=20&offset=0
    # 第1页
  GET
  /api/v1/workspace/public/studies?limit=20&offset=20
    # 第2页



## 📋 Table of Contents

- [Authentication](#authentication)
- [User Management](#user-management)
- [User Statistics](#user-statistics)
- [Workspace & Studies](#workspace--studies)
- [Chess Engine](#chess-engine)
- [Assignments](#assignments)
- [Blogs](#blogs)
- [Game Storage](#game-storage)
- [Tagger](#tagger)
- [Import/Export](#importexport)
- [Imitator](#imitator)

---

## 🔐 Authentication

**Base Path**: `/auth`

### Register with Email
```http
POST /auth/register
```

**Request Body**:
```json
{
  "identifier": "user@example.com",
  "identifier_type": "email",
  "password": "securePassword123",
  "username": "optional_username",
  "role": "student"
}
```

**Response**: `200 OK`
```json
{
  "message": "Verification code sent to email",
  "user_id": "uuid-string"
}
```

### Verify Email
```http
POST /auth/verify
```

**Request Body**:
```json
{
  "user_id": "uuid-string",
  "verification_code": "123456"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "username",
    "role": "student"
  }
}
```

### Login
```http
POST /auth/login
```

**Request Body**:
```json
{
  "identifier": "user@example.com",
  "password": "securePassword123"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

### Logout
```http
POST /auth/logout
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`

### Refresh Token
```http
POST /auth/refresh
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`
```json
{
  "access_token": "new-jwt-token",
  "token_type": "bearer"
}
```

---

## 👤 User Management

**Base Path**: `/api/v1/user`

### Get Current User Profile
```http
GET /api/v1/user/profile
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`
```json
{
  "id": "uuid",
  "username": "username",
  "identifier": "user@example.com",
  "role": "student",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Update User Profile
```http
PUT /api/v1/user/profile
```

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "username": "new_username",
  "self_intro": "I love chess!",
  "chess_rating": 1800,
  "favorite_opening": "Sicilian Defense"
}
```

**Response**: `200 OK`

---

## 📊 User Statistics

**Base Path**: `/api/v1/user/statistics`

### Get User Statistics
```http
GET /api/v1/user/statistics
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`
```json
{
  "total_online_seconds": 3600,
  "total_moves_count": 1250,
  "total_online_hours": 1.0
}
```

### Recalculate Moves Count
```http
POST /api/v1/user/statistics/recalculate-moves
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK`
```json
{
  "success": true,
  "total_moves_count": 1250,
  "message": "Successfully recalculated moves count: 1250"
}
```

### Record Heartbeat
```http
POST /api/v1/user/statistics/heartbeat
```

**Headers**: `Authorization: Bearer <token>`

**Description**: Frontend should call this every 60 seconds while user is active. Each call adds 60 seconds to online time.

**Response**: `200 OK`
```json
{
  "success": true,
  "total_online_seconds": 3660,
  "message": "Heartbeat recorded successfully"
}
```

---

## 📚 Workspace & Studies

**Base Path**: `/api/v1/workspace`

### Nodes (Files & Folders)

#### Get Root Children
```http
GET /api/v1/workspace/nodes/root/children
```

**Headers**: `Authorization: Bearer <token>`

**Response**: `200 OK` - List of nodes (folders and studies)

#### Create Node
```http
POST /api/v1/workspace/nodes
```

**Request Body**:
```json
{
  "node_type": "folder" | "study",
  "title": "My Study",
  "parent_id": "optional-parent-uuid",
  "visibility": "private" | "public"
}
```

#### Get Node Details
```http
GET /api/v1/workspace/nodes/{node_id}
```

#### Update Node
```http
PUT /api/v1/workspace/nodes/{node_id}
```

#### Delete Node
```http
DELETE /api/v1/workspace/nodes/{node_id}
```

#### Move Node
```http
POST /api/v1/workspace/nodes/{node_id}/move
```

**Request Body**:
```json
{
  "new_parent_id": "target-folder-uuid"
}
```

### Studies

#### Create Study
```http
POST /api/v1/workspace/studies
```

**Request Body**:
```json
{
  "title": "Sicilian Defense Study",
  "description": "Learning the Sicilian Defense",
  "parent_id": "optional-folder-uuid",
  "visibility": "private",
  "tags": ["opening", "sicilian"]
}
```

#### Get Study with Chapters
```http
GET /api/v1/workspace/studies/{study_id}
```

**Response**: Study metadata + list of chapters

#### Import PGN to New Study
```http
POST /api/v1/workspace/studies/import-pgn
```

**Request Body**:
```json
{
  "pgn_content": "[Event \"Game\"]\n1. e4 e5...",
  "base_title": "Imported Games",
  "parent_id": "optional-folder-uuid",
  "auto_split": true,
  "visibility": "private"
}
```

#### Import PGN to Existing Study
```http
POST /api/v1/workspace/studies/{study_id}/chapters/import-pgn
```

**Request Body**:
```json
{
  "pgn_content": "[Event \"Game\"]\n1. e4 e5..."
}
```

### Chapters

#### Get Chapters for Study
```http
GET /api/v1/workspace/studies/{study_id}/chapters
```

#### Create Chapter
```http
POST /api/v1/workspace/studies/{study_id}/chapters
```

**Request Body**:
```json
{
  "title": "Chapter 1: Main Line"
}
```

#### Update Chapter
```http
PUT /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}
```

**Request Body**:
```json
{
  "title": "Updated Chapter Title"
}
```

#### Delete Chapter
```http
DELETE /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}
```

#### Reorder Chapters
```http
POST /api/v1/workspace/studies/{study_id}/chapters/reorder
```

**Request Body**:
```json
{
  "order": ["chapter-id-1", "chapter-id-2", "chapter-id-3"]
}
```

#### Get Chapter Tree (Study Patch API)
```http
GET /api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree
```

**Response**:
```json
{
  "success": true,
  "tree": {
    "version": "v1",
    "rootId": "root",
    "nodes": {
      "root": {
        "id": "root",
        "parentId": null,
        "san": "",
        "children": ["move-1"],
        "comment": null,
        "nags": []
      }
    },
    "meta": {
      "result": "*"
    }
  },
  "starting_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

#### Update Chapter Tree (Save)
```http
PUT /api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree
```

**Request Body**: Same tree structure as GET response

**Response**:
```json
{
  "success": true
}
```

#### Export Chapter PGN
```http
GET /api/v1/workspace/studies/study-patch/chapter/{chapter_id}/pgn-export
```

**Response**:
```json
{
  "success": true,
  "pgn": "[Event \"...\"]\n1. e4 e5...",
  "filename": "Study - Chapter.pgn"
}
```

#### Export Study PGN (All Chapters)
```http
GET /api/v1/workspace/studies/study-patch/study/{study_id}/pgn-export
```

### Moves & Variations

#### Add Move
```http
POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves
```

**Request Body**:
```json
{
  "parent_id": "parent-move-id-or-root",
  "san": "e4",
  "uci": "e2e4",
  "move_number": 1,
  "color": "white",
  "rank": 0
}
```

#### Delete Move
```http
DELETE /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}
```

#### Add Variation
```http
POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/variations
```

**Request Body**: Same as Add Move, but `rank` > 0

#### Promote Variation
```http
PUT /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote
```

### Annotations (Comments)

#### Add Annotation
```http
POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations
```

**Request Body**:
```json
{
  "text": "This is a strong move because...",
  "nag": 1
}
```

#### Update Annotation
```http
PUT /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/annotations/{annotation_id}
```

**Request Body**:
```json
{
  "text": "Updated comment",
  "nag": 2,
  "version": 1
}
```

### PGN Clipping

#### Clip PGN from Position
```http
POST /api/v1/workspace/studies/{study_id}/pgn/clip
```

**Request Body**:
```json
{
  "chapter_id": "chapter-uuid",
  "mode": "clip" | "no_comment" | "raw" | "clean",
  "move_path": "main.12",
  "for_clipboard": true
}
```

### ShowDTO (Legacy - for old frontend)

#### Get Chapter ShowDTO
```http
GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show
```

**Note**: This is for the OLD frontend. Current frontend uses `/study-patch/chapter/{id}/tree`

#### Get Node FEN
```http
GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/fen/{node_id}
```

**Response**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "node_id": "move-id",
  "san": "e4",
  "uci": "e2e4",
  "move_number": 1,
  "color": "white"
}
```

---

## ♟️ Chess Engine

**Base Path**: `/api/chess`

### Analyze Position
```http
POST /api/chess/analyze
```

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "multipv": 3,
  "depth": 20
}
```

**Response**:
```json
{
  "lines": [
    {
      "depth": 20,
      "score_cp": 25,
      "score_mate": null,
      "pv": ["e2e4", "e7e5", "g1f3"],
      "pv_san": ["e4", "e5", "Nf3"]
    }
  ]
}
```

### Get Legal Moves
```http
POST /api/chess/legal-moves
```

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}
```

**Response**:
```json
{
  "moves": ["e2e4", "e2e3", "d2d4", ...]
}
```

### Validate Move
```http
POST /api/chess/validate-move
```

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": "e2e4"
}
```

**Response**:
```json
{
  "is_legal": true,
  "resulting_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
}
```

---

## 📝 Assignments

**Base Path**: `/assignments`

### Get All Assignments (Teacher)
```http
GET /assignments
```

**Headers**: `Authorization: Bearer <token>`

### Create Assignment (Teacher)
```http
POST /assignments
```

**Request Body**:
```json
{
  "title": "Endgame Practice",
  "description": "Complete the following endgame puzzles",
  "due_date": "2025-03-01T23:59:59Z",
  "assigned_to": ["student-id-1", "student-id-2"]
}
```

### Get Assignment Details
```http
GET /assignments/{assignment_id}
```

### Submit Assignment (Student)
```http
POST /assignments/{assignment_id}/submit
```

**Request Body**:
```json
{
  "content": "My solution...",
  "attachments": []
}
```

### Grade Assignment (Teacher)
```http
POST /assignments/{assignment_id}/grade
```

**Request Body**:
```json
{
  "student_id": "student-uuid",
  "score": 95,
  "feedback": "Excellent work!"
}
```

---

## 📰 Blogs

**Base Path**: `/api/blogs`

### Public Endpoints

#### Get All Published Blogs
```http
GET /api/blogs
```

**Query Parameters**:
- `category`: Filter by category
- `skip`: Pagination offset
- `limit`: Results per page

#### Get Blog by ID
```http
GET /api/blogs/{blog_id}
```

#### Search Blogs
```http
GET /api/blogs/search?q=chess+openings
```

### Admin Endpoints

**Base Path**: `/api/blog-admin`

#### Create Blog (Admin)
```http
POST /api/blog-admin/articles
```

**Headers**: `Authorization: Bearer <admin-token>`

**Request Body**:
```json
{
  "title": "Understanding the Sicilian Defense",
  "subtitle": "A comprehensive guide",
  "content": "Markdown content here...",
  "category": "openings",
  "tags": ["sicilian", "defense", "opening"],
  "status": "draft" | "published"
}
```

#### Update Blog (Admin)
```http
PUT /api/blog-admin/articles/{article_id}
```

#### Delete Blog (Admin)
```http
DELETE /api/blog-admin/articles/{article_id}
```

#### Upload Blog Image (Admin)
```http
POST /api/blog-admin/images
```

**Request**: `multipart/form-data` with image file

---

## 🎮 Game Storage

**Base Path**: `/api/games`

### Save Game
```http
POST /api/games
```

**Request Body**:
```json
{
  "pgn": "[Event \"Casual Game\"]\n1. e4 e5...",
  "white_player": "Player1",
  "black_player": "Player2",
  "result": "1-0"
}
```

### Get User Games
```http
GET /api/games
```

**Headers**: `Authorization: Bearer <token>`

### Get Game by ID
```http
GET /api/games/{game_id}
```

### Delete Game
```http
DELETE /api/games/{game_id}
```

---

## 🏷️ Tagger

**Base Path**: `/api/tagger`

### Get Players
```http
GET /api/tagger/players
```

**Query Parameters**:
- `search`: Search player name
- `limit`: Results limit

### Export Data
```http
GET /api/tagger/exports/{export_type}
```

**Export Types**: `players`, `games`, `openings`

---

## 📥 Import/Export

### Detect PGN Games
```http
POST /api/games/pgn/detect
```

**Request Body**:
```json
{
  "pgn_text": "[Event \"Game 1\"]\n1. e4 e5\n\n[Event \"Game 2\"]\n1. d4 d5"
}
```

**Response**:
```json
{
  "game_count": 2,
  "games": [
    {
      "index": 0,
      "headers": {
        "Event": "Game 1",
        "Site": "...",
        "Date": "..."
      },
      "movetext": "1. e4 e5"
    }
  ]
}
```

### Import FEN Position
```http
POST /api/v1/workspace/studies/{study_id}/chapters/import-fen
```

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "title": "Position after 1.e4"
}
```

---

## 🤖 Imitator

**Base Path**: `/api/imitator`

### Analyze Position with Imitator
```http
POST /api/imitator/analyze
```

**Request Body**:
```json
{
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "player_style": "aggressive" | "positional" | "solid"
}
```

---

## 🔧 Admin Endpoints

### User Role Management

**Base Path**: `/api/admin/roles`

#### Get All Users (Admin)
```http
GET /api/admin/roles/users
```

**Headers**: `Authorization: Bearer <admin-token>`

#### Update User Role (Admin)
```http
PUT /api/admin/roles/users/{user_id}/role
```

**Request Body**:
```json
{
  "role": "teacher" | "student" | "admin"
}
```

#### Deactivate User (Admin)
```http
POST /api/admin/roles/users/{user_id}/deactivate
```

---

## 🏥 Health & System

### Health Check
```http
GET /
```

**Response**:
```json
{
  "status": "ok",
  "service": "Catachess API",
  "version": "1.0.0"
}
```

### Health Check (Railway)
```http
GET /health
```

---

## 🔑 Authentication

All authenticated endpoints require a JWT token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

### Token Format
```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "role": "student" | "teacher" | "admin"
}
```

### Token Expiry
- Access tokens expire after **60 minutes**
- Refresh tokens can be used to get new access tokens

---

## ❌ Error Responses

### Standard Error Format
```json
{
  "detail": "Error message here"
}
```

### Common Status Codes
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## 📌 Notes

### Important Changes (2025-02-16)
1. ✅ User profile endpoint changed from `/user/profile` to `/api/v1/user/profile`
2. ✅ User statistics endpoints added at `/api/v1/user/statistics`
3. ✅ Auto-save interval changed from 15s to 5s
4. ✅ Study tree API moved to `/study-patch/chapter/{id}/tree`

### Rate Limits
- Chess engine analysis: **30 requests/minute** per IP
- Authentication endpoints: **10 requests/minute** per IP
- Other endpoints: **100 requests/minute** per user

### Pagination
Most list endpoints support pagination:
- `skip`: Number of items to skip (default: 0)
- `limit`: Number of items to return (default: 20, max: 100)

### Versioning
- Current API version: **v1**
- Version is included in the URL path: `/api/v1/...`
- Legacy endpoints without version prefix are being phased out

---

## 🆘 Support

For API questions or issues:
- GitHub Issues: https://github.com/steinitzchess2311-web/Catachess/issues
- Documentation: This file (API.md)

---

**Generated**: 2025-02-16
**Catachess Backend API v1.0.0**
