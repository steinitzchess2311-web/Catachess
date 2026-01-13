import os

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.domain.policies.limits import DiscussionLimits


class NestingDepthExceededError(Exception):
    pass


def get_max_depth() -> int:
    raw = os.getenv("DISCUSSION_MAX_REPLY_DEPTH")
    if raw and raw.isdigit():
        return max(1, int(raw))
    return DiscussionLimits.MAX_REPLY_NESTING_LEVEL


async def ensure_reply_depth(
    reply_repo: DiscussionReplyRepository, parent_reply_id: str | None
) -> None:
    depth = await get_reply_depth(reply_repo, parent_reply_id)
    if depth >= get_max_depth():
        raise NestingDepthExceededError("Reply nesting limit reached")


async def get_reply_depth(
    reply_repo: DiscussionReplyRepository, reply_id: str | None
) -> int:
    depth = 0
    current_id = reply_id
    while current_id:
        depth += 1
        reply = await reply_repo.get_by_id(current_id)
        if not reply:
            raise ValueError("Parent reply not found")
        current_id = reply.parent_reply_id
    return depth


async def can_add_reply(
    reply_repo: DiscussionReplyRepository, parent_reply_id: str | None
) -> bool:
    depth = await get_reply_depth(reply_repo, parent_reply_id)
    return depth < get_max_depth()
