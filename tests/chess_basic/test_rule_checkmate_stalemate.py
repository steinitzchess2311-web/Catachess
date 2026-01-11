"""
test_rule_checkmate_stalemate.py
将死与逼和测试

Checkmate and stalemate tests.
"""

import pytest
from backend.core.chess_basic.utils.fen import parse_fen
from backend.core.chess_basic.rule.api import is_checkmate, is_stalemate, is_check


class TestCheckmate:
    """将死测试 Checkmate tests"""

    def test_back_rank_mate(self):
        """底线将死 Back rank mate"""
        # 白后在底线将死黑王 White queen delivers back rank mate to black king
        fen = "4Q1k1/5ppp/8/8/8/8/8/7K b - - 0 1"
        state = parse_fen(fen)
        assert is_checkmate(state)

    def test_fools_mate(self):
        """傻瓜将死 Fool's mate"""
        fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1"
        state = parse_fen(fen)
        assert is_checkmate(state)

    def test_not_checkmate_if_can_block(self):
        """可以阻挡则不是将死 Not checkmate if can block"""
        # 设置一个将军但可以阻挡的局面 Set up check that can be blocked
        fen = "4k3/8/8/8/8/8/4R3/4K3 b - - 0 1"
        state = parse_fen(fen)
        # 被将军但不是将死 In check but not checkmate
        assert is_check(state)
        assert not is_checkmate(state)


class TestStalemate:
    """逼和测试 Stalemate tests"""

    def test_stalemate_king_trapped(self):
        """王被困住但未被将军 King trapped but not in check"""
        # 黑王没有合法走法且未被将军 Black king has no legal moves and not in check
        fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        state = parse_fen(fen)
        assert is_stalemate(state)

    def test_not_stalemate_if_in_check(self):
        """被将军则不是逼和 Not stalemate if in check"""
        fen = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        state = parse_fen(fen)
        # 被将军，所以不是逼和 In check, so not stalemate
        assert not is_stalemate(state)

    def test_not_stalemate_if_has_legal_move(self):
        """有合法走法则不是逼和 Not stalemate if has legal moves"""
        fen = "7k/8/6K1/8/8/8/8/8 b - - 0 1"
        state = parse_fen(fen)
        # 有合法走法 Has legal moves
        assert not is_stalemate(state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
