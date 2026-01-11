"""
Discussion reply commands.
"""

from dataclasses import dataclass

from workspace.domain.policies.limits import DiscussionLimits


@dataclass
class AddReplyCommand:
    """Command to add a reply."""

    thread_id: str
    author_id: str
    content: str
    parent_reply_id: str | None = None
    quote_reply_id: str | None = None

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Reply content cannot be empty")
        if len(self.content) > DiscussionLimits.MAX_REPLY_LENGTH:
            raise ValueError("Reply content too long")


@dataclass
class EditReplyCommand:
    """Command to edit a reply."""

    reply_id: str
    content: str
    actor_id: str
    version: int

    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Reply content cannot be empty")
        if len(self.content) > DiscussionLimits.MAX_REPLY_LENGTH:
            raise ValueError("Reply content too long")


@dataclass
class DeleteReplyCommand:
    """Command to delete a reply."""

    reply_id: str
    actor_id: str
