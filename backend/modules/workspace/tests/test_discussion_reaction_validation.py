"""
Discussion reaction validation tests.
"""

import pytest

from workspace.domain.models.discussion_reaction import AddReactionCommand


def test_reaction_rejects_invalid_emoji():
    with pytest.raises(ValueError):
        AddReactionCommand(
            target_id="reply-1",
            target_type="reply",
            user_id="user-1",
            emoji="not-allowed",
        )
