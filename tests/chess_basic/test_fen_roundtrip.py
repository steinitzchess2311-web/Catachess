"""
test_fen_roundtrip.py
FEN 解析与还原测试

FEN parsing and serialization tests.
"""

import pytest
from backend.core.chess_basic.utils.fen import parse_fen, board_to_fen, STARTING_FEN


class TestFENRoundtrip:
    """FEN 往返测试 FEN roundtrip tests"""

    def test_starting_position_roundtrip(self):
        """起始位置 FEN 往返 Starting position FEN roundtrip"""
        state = parse_fen(STARTING_FEN)
        fen = board_to_fen(state)
        assert fen == STARTING_FEN

    def test_custom_position_roundtrip(self):
        """自定义位置 FEN 往返 Custom position FEN roundtrip"""
        original_fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        state = parse_fen(original_fen)
        fen = board_to_fen(state)
        assert fen == original_fen

    def test_en_passant_square_preserved(self):
        """吃过路兵目标格保留 En passant square preserved"""
        original_fen = "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2"
        state = parse_fen(original_fen)
        fen = board_to_fen(state)
        assert fen == original_fen

    def test_castling_rights_preserved(self):
        """王车易位权利保留 Castling rights preserved"""
        # 只有白方王侧易位 Only white kingside castling
        original_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w K - 0 1"
        state = parse_fen(original_fen)
        fen = board_to_fen(state)
        assert fen == original_fen

    def test_halfmove_clock_preserved(self):
        """半回合计数保留 Halfmove clock preserved"""
        original_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 10 5"
        state = parse_fen(original_fen)
        fen = board_to_fen(state)
        assert fen == original_fen


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
