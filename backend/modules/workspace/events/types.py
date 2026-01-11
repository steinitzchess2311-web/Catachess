"""
Event type definitions for the workspace system.

ALL write operations MUST produce events. This file defines the complete
event taxonomy that drives the system's reactive architecture.

Event Naming Convention: {domain}.{action}
- domain: workspace, folder, study, acl, discussion, notification, presence, etc.
- action: created, updated, deleted, moved, etc.
"""

from enum import Enum


class EventType(str, Enum):
    """
    Complete enumeration of all events in the system.

    Events are the "nervous system" of the application:
    - Drive WebSocket real-time updates
    - Trigger notifications
    - Update search indexes
    - Record activity logs
    - Enable undo/redo
    - Support audit trails
    """

    # ===== Node Operations =====
    WORKSPACE_CREATED = "workspace.created"
    WORKSPACE_UPDATED = "workspace.updated"
    WORKSPACE_DELETED = "workspace.deleted"
    WORKSPACE_MOVED = "workspace.moved"

    FOLDER_CREATED = "folder.created"
    FOLDER_RENAMED = "folder.renamed"
    FOLDER_DELETED = "folder.deleted"
    FOLDER_MOVED = "folder.moved"

    STUDY_CREATED = "study.created"
    STUDY_UPDATED = "study.updated"
    STUDY_DELETED = "study.deleted"
    STUDY_MOVED = "study.moved"

    LAYOUT_UPDATED = "layout.updated"  # Drag/drop position, auto-arrange

    # ===== ACL & Permissions =====
    ACL_SHARED = "acl.shared"  # Node shared with user
    ACL_REVOKED = "acl.revoked"  # Share revoked
    ACL_ROLE_CHANGED = "acl.role_changed"  # User role changed
    ACL_LINK_CREATED = "acl.link_created"  # Share link created
    ACL_LINK_REVOKED = "acl.link_revoked"  # Share link revoked
    ACL_INHERITED = "acl.inherited"  # ACL inherited to children
    ACL_INHERITANCE_BROKEN = "acl.inheritance_broken"  # Inheritance broken

    # ===== Study Content =====
    # Chapter operations
    STUDY_CHAPTER_IMPORTED = "study.chapter.imported"  # PGN imported
    STUDY_CHAPTER_SPLIT_TO_FOLDER = "study.chapter.split_to_folder"  # >64 chapters
    STUDY_CHAPTER_CREATED = "study.chapter.created"
    STUDY_CHAPTER_RENAMED = "study.chapter.renamed"
    STUDY_CHAPTER_DELETED = "study.chapter.deleted"
    STUDY_CHAPTER_REORDERED = "study.chapter.reordered"

    # Move & variation operations
    STUDY_MOVE_ADDED = "study.move.added"
    STUDY_MOVE_DELETED = "study.move.deleted"
    STUDY_VARIATION_PROMOTED = "study.variation.promoted"
    STUDY_VARIATION_DEMOTED = "study.variation.demoted"
    STUDY_VARIATION_REORDERED = "study.variation.reordered"

    # Move annotation (professional annotations, exported with PGN)
    STUDY_MOVE_ANNOTATION_ADDED = "study.move_annotation.added"
    STUDY_MOVE_ANNOTATION_UPDATED = "study.move_annotation.updated"
    STUDY_MOVE_ANNOTATION_DELETED = "study.move_annotation.deleted"

    # Versioning
    STUDY_SNAPSHOT_CREATED = "study.snapshot.created"
    STUDY_ROLLBACK = "study.rollback"

    # ===== Discussion System (User comments, NOT exported with PGN) =====
    DISCUSSION_THREAD_CREATED = "discussion.thread.created"
    DISCUSSION_THREAD_UPDATED = "discussion.thread.updated"
    DISCUSSION_THREAD_DELETED = "discussion.thread.deleted"
    DISCUSSION_THREAD_PINNED = "discussion.thread.pinned"
    DISCUSSION_THREAD_RESOLVED = "discussion.thread.resolved"
    DISCUSSION_THREAD_REOPENED = "discussion.thread.reopened"

    DISCUSSION_REPLY_ADDED = "discussion.reply.added"
    DISCUSSION_REPLY_EDITED = "discussion.reply.edited"
    DISCUSSION_REPLY_DELETED = "discussion.reply.deleted"

    DISCUSSION_REACTION_ADDED = "discussion.reaction.added"
    DISCUSSION_REACTION_REMOVED = "discussion.reaction.removed"

    DISCUSSION_MENTION = "discussion.mention"  # @mention user

    # ===== Export System =====
    PGN_EXPORT_REQUESTED = "pgn.export.requested"
    PGN_EXPORT_COMPLETED = "pgn.export.completed"
    PGN_EXPORT_FAILED = "pgn.export.failed"
    PGN_CLIPBOARD_GENERATED = "pgn.clipboard.generated"  # Clean PGN copied

    # ===== Collaboration & Presence =====
    PRESENCE_USER_JOINED = "presence.user_joined"
    PRESENCE_USER_LEFT = "presence.user_left"
    PRESENCE_USER_IDLE = "presence.user_idle"
    PRESENCE_USER_ACTIVE = "presence.user_active"
    PRESENCE_CURSOR_MOVED = "presence.cursor_moved"

    # ===== Notification System =====
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_DISMISSED = "notification.dismissed"
    NOTIFICATION_BULK_READ = "notification.bulk_read"

    # ===== Trash & Cleanup =====
    NODE_SOFT_DELETED = "node.soft_deleted"  # Moved to trash
    NODE_RESTORED = "node.restored"  # Restored from trash
    NODE_PERMANENTLY_DELETED = "node.permanently_deleted"  # Gone forever


# Event payload field conventions
class EventField:
    """
    Standard field names for event payloads.

    Consistency in field naming makes event processing easier.
    """
    EVENT_ID = "event_id"
    TYPE = "type"
    ACTOR_ID = "actor_id"
    TARGET_ID = "target_id"
    TARGET_TYPE = "target_type"
    TIMESTAMP = "timestamp"
    VERSION = "version"  # Object version (for optimistic locking)
    PAYLOAD = "payload"  # Minimal diff or change description

    # Common payload fields
    OLD_VALUE = "old_value"
    NEW_VALUE = "new_value"
    PARENT_ID = "parent_id"
    NODE_PATH = "node_path"
    USER_ID = "user_id"
    PERMISSION = "permission"
    REASON = "reason"
