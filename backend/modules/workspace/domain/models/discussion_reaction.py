"""
Discussion reaction commands.
"""

from dataclasses import dataclass

from workspace.domain.policies.limits import DiscussionLimits


@dataclass
class AddReactionCommand:
    """Command to add a reaction."""

    target_id: str
    target_type: str
    user_id: str
    emoji: str

    def __post_init__(self) -> None:
        if not self.emoji:
            raise ValueError("Emoji cannot be empty")
        if self.emoji not in DiscussionLimits.ALLOWED_REACTION_EMOJIS:
            raise ValueError("Emoji is not allowed")


@dataclass
class RemoveReactionCommand:
    """Command to remove a reaction."""

    reaction_id: str
    user_id: str
