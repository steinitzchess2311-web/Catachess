"""
test_rule_legal_basic.py
基础规则合法性测试

Basic rule legality tests.
"""

import pytest
from backend.core.chess_basic.types import Move, Square
from backend.core.chess_basic.utils.fen import get_starting_position
from backend.core.chess_basic.rule.api import is_legal_move, generate_legal_moves


class TestBasicLegality:
    """基础合法性测试 Basic legality tests"""

    def test_starting_position_has_20_legal_moves(self):
        """起始位置有 20 个合法走法 Starting position has 20 legal moves"""
        state = get_starting_position()
        legal_moves = generate_legal_moves(state)
        assert len(legal_moves) == 20

    def test_pawn_can_move_forward_one(self):
        """兵可以前进一步 Pawn can move forward one square"""
        state = get_starting_position()
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e3"))
        assert is_legal_move(state, move)

    def test_pawn_can_move_forward_two_from_start(self):
        """兵可以从起始位置前进两步 Pawn can move two squares from start"""
        state = get_starting_position()
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        assert is_legal_move(state, move)

    def test_knight_can_jump(self):
        """马可以跳跃 Knight can jump"""
        state = get_starting_position()
        move = Move(Square.from_algebraic("g1"), Square.from_algebraic("f3"))
        assert is_legal_move(state, move)

    def test_pawn_cannot_move_backward(self):
        """兵不能后退 Pawn cannot move backward"""
        state = get_starting_position()
        # 白兵尝试后退 White pawn trying to move backward
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e1"))
        assert not is_legal_move(state, move)

    def test_piece_cannot_move_to_square_with_own_piece(self):
        """棋子不能移动到己方棋子所在格 Piece cannot move to square with own piece"""
        state = get_starting_position()
        # 尝试把马移到兵的位置 Try to move knight to pawn's square
        move = Move(Square.from_algebraic("g1"), Square.from_algebraic("g2"))
        assert not is_legal_move(state, move)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
