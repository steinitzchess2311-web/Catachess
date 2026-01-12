"""Database table definitions"""

from workspace.db.tables.acl import ACL, ShareLink
from workspace.db.tables.activity_log import ActivityLog
from workspace.db.tables.events import Event
from workspace.db.tables.notifications import Notification
from workspace.db.tables.notification_preferences import NotificationPreference
from workspace.db.tables.nodes import Node
from workspace.db.tables.studies import Chapter, Study
from workspace.db.tables.variations import MoveAnnotation, Variation
from workspace.db.tables.discussion_threads import DiscussionThread, ThreadType
from workspace.db.tables.discussion_replies import DiscussionReply
from workspace.db.tables.discussion_reactions import DiscussionReaction
from workspace.db.tables.search_index import SearchIndex
from workspace.db.tables.audit_log import AuditLog
from workspace.db.tables.users import User

__all__ = [
    "Node",
    "ACL",
    "ShareLink",
    "Event",
    "Study",
    "Chapter",
    "Variation",
    "MoveAnnotation",
    "DiscussionThread",
    "DiscussionReply",
    "DiscussionReaction",
    "ThreadType",
    "SearchIndex",
    "Notification",
    "NotificationPreference",
]
