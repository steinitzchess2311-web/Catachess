"""
Core type definitions and enums for the workspace system.

These types form the protocol foundation and should NOT be changed lightly
once deployed, as they affect data structure and API contracts.
"""

from enum import Enum


class NodeType(str, Enum):
    """
    Node type in the workspace tree.

    - WORKSPACE: Top-level workspace container
    - FOLDER: Folder node (supports infinite nesting)
    - STUDY: Study node (leaf node containing chess content)

    Future extensions may include: file, board, snippet, etc.
    """
    WORKSPACE = "workspace"
    FOLDER = "folder"
    STUDY = "study"


class Permission(str, Enum):
    """
    Permission levels for shared objects.

    Hierarchy (from highest to lowest):
    - OWNER: Full permissions (delete, transfer ownership)
    - ADMIN: Manage members and settings
    - EDITOR: Edit content
    - COMMENTER: Only comment/discuss
    - VIEWER: Read-only
    """
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    COMMENTER = "commenter"
    VIEWER = "viewer"

    @classmethod
    def can_read(cls, permission: "Permission") -> bool:
        """Check if permission allows reading."""
        return permission in {cls.OWNER, cls.ADMIN, cls.EDITOR, cls.COMMENTER, cls.VIEWER}

    @classmethod
    def can_write(cls, permission: "Permission") -> bool:
        """Check if permission allows writing."""
        return permission in {cls.OWNER, cls.ADMIN, cls.EDITOR}

    @classmethod
    def can_manage_acl(cls, permission: "Permission") -> bool:
        """Check if permission allows managing ACL."""
        return permission in {cls.OWNER, cls.ADMIN}

    @classmethod
    def can_delete(cls, permission: "Permission") -> bool:
        """Check if permission allows deletion."""
        return permission in {cls.OWNER, cls.ADMIN}


class Visibility(str, Enum):
    """
    Visibility settings for objects.

    - PRIVATE: Only visible to owner and explicitly shared users
    - SHARED: Shared with specific users
    - PUBLIC: Publicly visible (future feature)
    """
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"  # Future feature


class Priority(str, Enum):
    """
    Priority level for variations in chess studies.

    - MAIN: Main variation (primary line)
    - SECONDARY: Secondary variation (alternative)
    - DRAFT: Draft variation (work in progress)
    """
    MAIN = "main"
    SECONDARY = "secondary"
    DRAFT = "draft"


class ThreadType(str, Enum):
    """
    Discussion thread type.

    - QUESTION: Question thread (can be marked as resolved)
    - SUGGESTION: Suggestion or improvement idea
    - NOTE: General note or comment
    """
    QUESTION = "question"
    SUGGESTION = "suggestion"
    NOTE = "note"


class PresenceStatus(str, Enum):
    """
    User presence status in real-time collaboration.

    - ACTIVE: Actively working (within 30s)
    - IDLE: Idle (30s - 5min)
    - AWAY: Away (> 5min)
    """
    ACTIVE = "active"
    IDLE = "idle"
    AWAY = "away"


class NotificationChannel(str, Enum):
    """
    Notification delivery channel.

    - IN_APP: In-app notification (required)
    - EMAIL: Email notification (optional)
    - PUSH: Push notification (future)
    """
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"  # Future feature


class DigestFrequency(str, Enum):
    """
    Notification digest frequency.

    - REALTIME: Send immediately
    - DAILY: Daily digest
    - WEEKLY: Weekly digest
    """
    REALTIME = "realtime"
    DAILY = "daily"
    WEEKLY = "weekly"


class ExportFormat(str, Enum):
    """
    Export format options.

    - PGN: Single PGN file
    - ZIP: ZIP archive (for multiple files)
    """
    PGN = "pgn"
    ZIP = "zip"


class ExportJobStatus(str, Enum):
    """
    Export job status.

    - PENDING: Job created, not started
    - RUNNING: Job in progress
    - COMPLETED: Job completed successfully
    - FAILED: Job failed
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
