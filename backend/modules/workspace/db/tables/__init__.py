"""Database table definitions"""

from workspace.db.tables.acl import ACL, ShareLink
from workspace.db.tables.events import Event
from workspace.db.tables.nodes import Node
from workspace.db.tables.studies import Chapter, Study
from workspace.db.tables.variations import MoveAnnotation, Variation
from workspace.db.tables.discussion_threads import DiscussionThread, ThreadType
from workspace.db.tables.discussion_replies import DiscussionReply
from workspace.db.tables.discussion_reactions import DiscussionReaction
from workspace.db.tables.search_index import SearchIndex

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
]
