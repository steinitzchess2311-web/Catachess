"""
chess_basic.rule.perft
规则正确性与性能验证工具

Performance test and move generation verification tool.

Perft (Performance Test) is used to verify move generation correctness
by counting all possible positions at a given depth.
"""

from ..types import BoardState, Move
from .legality import is_move_legal
from .apply import apply_move_unchecked
from .movegen import generate_pseudo_legal_moves


def perft(state: BoardState, depth: int) -> int:
    """
    计算指定深度的所有可能局面数
    Count all possible positions at given depth

    Args:
        state: Starting board state
        depth: Search depth

    Returns:
        Number of leaf nodes at specified depth
    """
    if depth == 0:
        return 1

    count = 0
    pseudo_legal = generate_pseudo_legal_moves(state)

    for move in pseudo_legal:
        if is_move_legal(state, move):
            new_state = apply_move_unchecked(state, move)
            count += perft(new_state, depth - 1)

    return count


def perft_divide(state: BoardState, depth: int) -> dict[str, int]:
    """
    分别计算每个走法的 perft 值（用于调试）
    Calculate perft value for each move separately (for debugging)

    Args:
        state: Starting board state
        depth: Search depth

    Returns:
        Dictionary mapping move UCI to node count
    """
    results = {}
    pseudo_legal = generate_pseudo_legal_moves(state)

    for move in pseudo_legal:
        if is_move_legal(state, move):
            new_state = apply_move_unchecked(state, move)
            if depth == 1:
                count = 1
            else:
                count = perft(new_state, depth - 1)
            results[move.to_uci()] = count

    return results


def verify_perft(state: BoardState, depth: int, expected: int) -> bool:
    """
    验证 perft 结果是否符合预期
    Verify perft result matches expected value

    Args:
        state: Starting board state
        depth: Search depth
        expected: Expected node count

    Returns:
        True if result matches expected, False otherwise
    """
    actual = perft(state, depth)
    if actual != expected:
        print(f"Perft verification failed at depth {depth}:")
        print(f"  Expected: {expected}")
        print(f"  Actual:   {actual}")
        return False
    return True


# 标准起始位置的 perft 值（用于验证）
# Standard perft values for starting position (for verification)
STARTING_POSITION_PERFT_VALUES = {
    0: 1,
    1: 20,
    2: 400,
    3: 8_902,
    4: 197_281,
    5: 4_865_609,
    6: 119_060_324,
}


def run_perft_tests(verbose: bool = True) -> bool:
    """
    运行标准 perft 测试
    Run standard perft tests

    Args:
        verbose: Whether to print results

    Returns:
        True if all tests pass, False otherwise
    """
    from ..utils.fen import get_starting_position

    state = get_starting_position()
    all_passed = True

    for depth in range(1, 5):  # 测试深度 1-4 Test depths 1-4
        expected = STARTING_POSITION_PERFT_VALUES[depth]
        if verbose:
            print(f"Running perft({depth})...", end=" ")

        actual = perft(state, depth)

        if actual == expected:
            if verbose:
                print(f"✓ {actual:,} nodes")
        else:
            if verbose:
                print(f"✗ Expected {expected:,}, got {actual:,}")
            all_passed = False

    return all_passed
