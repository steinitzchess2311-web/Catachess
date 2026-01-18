import pytest
from backend.core.real_pgn.parser import parse_pgn
from backend.core.real_pgn.builder import build_pgn
from backend.core.real_pgn.fen import build_fen_index
from backend.core.real_pgn.show import build_show

SAMPLE_PGN = """
[Event "Sample Game"]
[Site "My Computer"]
[Date "2024.01.01"]
[Round "1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 (2... f6 3. Bc4) 3. Bb5 a6 *
"""

def test_parse_and_build_cycle():
    """
    Tests that parsing a PGN and then building it back results in a similar PGN.
    This is a good integration test for the parser and builder.
    """
    # 1. Parse the PGN
    tree = parse_pgn(SAMPLE_PGN)
    
    # Assertions for the parser
    assert tree is not None
    assert tree.meta.headers["Event"] == "Sample Game"
    assert tree.meta.result == "1-0"
    assert len(tree.nodes) > 5 # root + 5 moves + 1 variation move

    # Find specific nodes to check relationships
    e4_node = tree.nodes[tree.nodes[tree.root_id].variations[0]]
    assert e4_node.san == "e4"
    
    e5_node = tree.nodes[e4_node.variations[0]]
    assert e5_node.san == "e5"

    nf3_node = tree.nodes[e5_node.variations[0]]
    assert nf3_node.san == "Nf3"
    assert len(nf3_node.variations) == 2 # Nc6 and f6

    # 2. Build the PGN back
    rebuilt_pgn = build_pgn(tree)
    
    # Assertions for the builder
    assert '[Event "Sample Game"]' in rebuilt_pgn
    assert "1. e4 e5" in rebuilt_pgn
    assert "(2... f6 3. Bc4)" in rebuilt_pgn # Note: builder adds spaces
    assert "3. Bb5 a6" in rebuilt_pgn
    assert rebuilt_pgn.strip().endswith("1-0")

def test_fen_indexer():
    """
    Tests the build_fen_index function.
    """
    tree = parse_pgn(SAMPLE_PGN)
    fen_index = build_fen_index(tree)
    
    assert len(fen_index) == len(tree.nodes)
    
    # Get FEN for a specific position (after 3. Bb5)
    root_node = tree.nodes[tree.root_id]
    e4_node = tree.nodes[root_node.variations[0]]
    e5_node = tree.nodes[e4_node.variations[0]]
    nf3_node = tree.nodes[e5_node.variations[0]]
    nc6_node = tree.nodes[nf3_node.variations[0]]
    bb5_node_id = nc6_node.variations[0] # This is 3. Bb5
    
    expected_fen = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
    assert fen_index[bb5_node_id] == expected_fen
def test_show_dto_builder():
    """
    Tests the build_show function.
    """
    tree = parse_pgn(SAMPLE_PGN)
    show_dto = build_show(tree)

    assert "headers" in show_dto
    assert "nodes" in show_dto
    assert "render_tokens" in show_dto

    assert len(show_dto["headers"]) == 7
    assert len(show_dto["nodes"]) == len(tree.nodes)

    # Check for token structure
    tokens = show_dto["render_tokens"]
    assert tokens[0]["type"] == "move"
    assert tokens[0]["san"] == "e4"
    
    # Find the variation start token
    var_start_found = any(t["type"] == "variation_start" for t in tokens)
    assert var_start_found

    var_end_found = any(t["type"] == "variation_end" for t in tokens)
    assert var_end_found

