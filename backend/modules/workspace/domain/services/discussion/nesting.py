"""
Reply nesting helpers.
"""

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.domain.policies.limits import DiscussionLimits


async def ensure_reply_depth(
    reply_repo: DiscussionReplyRepository, parent_reply_id: str | None
) -> None:
    depth = 0
    current_id = parent_reply_id
    while current_id:
        depth += 1
        if depth >= DiscussionLimits.MAX_REPLY_NESTING_LEVEL - 1:
            raise ValueError("Reply nesting limit reached")
        reply = await reply_repo.get_by_id(current_id)
        if not reply:
            raise ValueError("Parent reply not found")
        current_id = reply.parent_reply_id
