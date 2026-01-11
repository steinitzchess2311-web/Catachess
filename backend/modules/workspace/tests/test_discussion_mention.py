"""
Discussion mention parsing tests.
"""

from workspace.domain.services.discussion_mentions import extract_mentions


def test_extract_mentions_unique():
    text = "Hi @alice and @bob. Thanks @alice!"
    mentions = extract_mentions(text)
    assert sorted(mentions) == ["alice", "bob"]
