"""
Discussion thread commands.
"""

from dataclasses import dataclass

from workspace.domain.policies.limits import DiscussionLimits


@dataclass
class CreateThreadCommand:
    """Command to create a discussion thread."""

    target_id: str
    target_type: str
    author_id: str
    title: str
    content: str
    thread_type: str

    def __post_init__(self) -> None:
        if not self.title or len(self.title) > DiscussionLimits.MAX_THREAD_TITLE_LENGTH:
            raise ValueError("Invalid thread title length")
        if not self.content:
            raise ValueError("Thread content cannot be empty")


@dataclass
class UpdateThreadCommand:
    """Command to update a discussion thread."""

    thread_id: str
    title: str
    content: str
    actor_id: str
    version: int

    def __post_init__(self) -> None:
        if not self.title or len(self.title) > DiscussionLimits.MAX_THREAD_TITLE_LENGTH:
            raise ValueError("Invalid thread title length")
        if not self.content:
            raise ValueError("Thread content cannot be empty")


@dataclass
class ResolveThreadCommand:
    """Command to resolve or reopen a thread."""

    thread_id: str
    actor_id: str
    resolved: bool
    version: int


@dataclass
class PinThreadCommand:
    """Command to pin or unpin a thread."""

    thread_id: str
    actor_id: str
    pinned: bool
    version: int
