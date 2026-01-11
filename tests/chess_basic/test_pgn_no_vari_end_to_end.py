"""
test_pgn_no_vari_end_to_end.py
主线 PGN 全流程测试

Mainline PGN end-to-end tests.
"""

import pytest
from backend.core.chess_basic.types import Move, Square
from backend.core.chess_basic.utils.fen import get_starting_position
from backend.core.chess_basic.rule.api import apply_move
from backend.core.chess_basic.pgn.no_vari.writer import PGNWriterNoVari
from backend.core.chess_basic.utils.san import move_to_san


class TestPGNNoVariEndToEnd:
    """主线 PGN 端到端测试 Mainline PGN end-to-end tests"""

    def test_simple_game_pgn(self):
        """简单对局 PGN Simple game PGN"""
        writer = PGNWriterNoVari()
        writer.set_players("Player1", "Player2")
        writer.set_event("Test Game", "Test Site")

        state = get_starting_position()

        # 1. e4
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)
        state = apply_move(state, move)

        # 1... e5
        move = Move(Square.from_algebraic("e7"), Square.from_algebraic("e5"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)
        state = apply_move(state, move)

        # 2. Nf3
        move = Move(Square.from_algebraic("g1"), Square.from_algebraic("f3"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)

        pgn = writer.to_pgn_string()

        # 验证 PGN 包含必要元素 Verify PGN contains necessary elements
        assert "Player1" in pgn
        assert "Player2" in pgn
        assert "Test Game" in pgn
        assert "1. e4 e5" in pgn or "1. e4" in pgn
        assert "Nf3" in pgn

    def test_pgn_with_comments(self):
        """带评注的 PGN PGN with comments"""
        writer = PGNWriterNoVari()

        state = get_starting_position()

        # 1. e4
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)
        writer.add_comment("Best by test!")

        pgn = writer.to_pgn_string()

        # 验证评注 Verify comment
        assert "Best by test!" in pgn

    def test_move_count(self):
        """走法计数 Move count"""
        writer = PGNWriterNoVari()
        state = get_starting_position()

        assert writer.get_move_count() == 0

        # 添加走法 Add move
        move = Move(Square.from_algebraic("e2"), Square.from_algebraic("e4"))
        san = move_to_san(move, state)
        writer.add_move(move, state, san)

        assert writer.get_move_count() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
