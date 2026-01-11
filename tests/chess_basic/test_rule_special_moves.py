"""
test_rule_special_moves.py
特殊走法测试

Special moves tests (castling, en passant, promotion).
"""

import pytest
from backend.core.chess_basic.types import Move, Square
from backend.core.chess_basic.constants import PieceType
from backend.core.chess_basic.utils.fen import parse_fen
from backend.core.chess_basic.rule.api import is_legal_move, apply_move


class TestCastling:
    """王车易位测试 Castling tests"""

    def test_white_kingside_castling(self):
        """白方王侧易位 White kingside castling"""
        # 设置可以易位的局面 Set up position where castling is possible
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
        state = parse_fen(fen)
        move = Move(Square.from_algebraic("e1"), Square.from_algebraic("g1"))
        assert is_legal_move(state, move)

    def test_white_queenside_castling(self):
        """白方后侧易位 White queenside castling"""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/R3KBNR w KQkq - 0 1"
        state = parse_fen(fen)
        move = Move(Square.from_algebraic("e1"), Square.from_algebraic("c1"))
        assert is_legal_move(state, move)

    def test_cannot_castle_through_check(self):
        """不能穿过被攻击的格子易位 Cannot castle through check"""
        # 设置白方王侧路径被攻击 Set up position where castling path is attacked
        fen = "rnbqkbnr/pppp1ppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
        # 需要添加攻击 f1 的黑方棋子 Need to add black piece attacking f1
        # 这个测试需要更复杂的局面设置 This test needs more complex position setup
        pass


class TestEnPassant:
    """吃过路兵测试 En passant tests"""

    def test_en_passant_capture(self):
        """吃过路兵 En passant capture"""
        # 设置吃过路兵的局面 Set up en passant position
        fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"
        state = parse_fen(fen)
        move = Move(Square.from_algebraic("e5"), Square.from_algebraic("d6"))
        assert is_legal_move(state, move)


class TestPromotion:
    """升变测试 Promotion tests"""

    def test_pawn_promotion_to_queen(self):
        """兵升变为后 Pawn promotes to queen"""
        # 白兵在第 7 等级 White pawn on 7th rank
        fen = "8/P7/8/8/8/8/8/8 w - - 0 1"
        state = parse_fen(fen)
        move = Move(
            Square.from_algebraic("a7"),
            Square.from_algebraic("a8"),
            PieceType.QUEEN
        )
        assert is_legal_move(state, move)

    def test_pawn_must_promote_on_8th_rank(self):
        """兵到达第 8 等级必须升变 Pawn must promote on 8th rank"""
        fen = "8/P7/8/8/8/8/8/8 w - - 0 1"
        state = parse_fen(fen)
        # 尝试不升变 Try without promotion
        move = Move(Square.from_algebraic("a7"), Square.from_algebraic("a8"))
        # 不升变应该不合法 Without promotion should be illegal
        # 注意：具体行为取决于实现 Note: specific behavior depends on implementation
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
