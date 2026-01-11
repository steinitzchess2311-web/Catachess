"""
test_pgn_vari_end_to_end.py
分支 PGN 全流程测试

Variation PGN end-to-end tests.
"""

import pytest
from backend.core.chess_basic.types import Move, Square
from backend.core.chess_basic.utils.fen import get_starting_position
from backend.core.chess_basic.rule.api import apply_move
from backend.core.chess_basic.pgn.vari.writer import PGNWriterVari
from backend.core.chess_basic.utils.san import move_to_san


class TestPGNVariEndToEnd:
    """分支 PGN 端到端测试 Variation PGN end-to-end tests"""

    def test_simple_variation(self):
        """简单分支 Simple variation"""
        writer = PGNWriterVari()
        writer.set_players("Player1", "Player2")

        state = get_starting_position()

        # 主线：1. e4
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)
        state_after_e4 = apply_move(state, move)

        # 主线：1... e5
        move = Move(Square.from_algebraic("e7"), Square.from_algebraic("e5"))
        san = move_to_san(move, state_after_e4)
        writer.add_move(move, state_after_e4, san)

        # 开始分支（探索 1... c5 替代 e5）
        # Start variation (explore 1... c5 instead of e5)
        writer.start_variation()
        move_alt = Move(Square.from_algebraic("c7"), Square.from_algebraic("c5"))
        san_alt = move_to_san(move_alt, state_after_e4)
        writer.add_move(move_alt, state_after_e4, san_alt)
        writer.end_variation()

        pgn = writer.to_pgn_string()

        # 验证包含主线和分支 Verify contains mainline and variation
        assert "e4" in pgn
        assert "e5" in pgn
        assert "c5" in pgn
        # 分支应该在括号中 Variation should be in parentheses
        assert "(" in pgn and ")" in pgn

    def test_nested_variations(self):
        """嵌套分支 Nested variations"""
        writer = PGNWriterVari()

        state = get_starting_position()

        # 主线：1. e4 e5
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)
        state = apply_move(state, move)

        move = Move(Square.from_algebraic("e7"), Square.from_algebraic("e5"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)

        # 添加分支 Add variation
        writer.start_variation()
        state_var = get_starting_position()
        state_var = apply_move(state_var, Move(Square.from_algebraic("e2"), Square.from_algebraic("e4")))
        move_alt = Move(Square.from_algebraic("c7"), Square.from_algebraic("c5"))
        san_alt = move_to_san(move_alt, state_var)
        writer.add_move(move_alt, state_var, san_alt)
        writer.end_variation()

        pgn = writer.to_pgn_string()

        # 验证生成了 PGN Verify PGN generated
        assert len(pgn) > 0
        assert writer.get_move_count() == 2  # 主线有 2 个走法 Mainline has 2 moves


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
