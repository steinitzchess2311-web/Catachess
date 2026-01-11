"""
Tests for chapter detection and study splitting.
"""

import pytest

from workspace.pgn.chapter_detector import (
    detect_chapters,
    calculate_split_distribution,
    split_games_into_studies,
    suggest_study_names,
    MAX_CHAPTERS_PER_STUDY,
)
from workspace.pgn.parser.split_games import PGNGame


def create_mock_games(count: int) -> list[PGNGame]:
    """Create mock PGN games for testing."""
    games = []
    for i in range(count):
        game = PGNGame(
            headers={"Event": f"Game {i+1}", "White": "A", "Black": "B"},
            moves=f"1. e4 e5 *",
            raw_content=f"[Event \"Game {i+1}\"]\n1. e4 e5 *",
            game_number=i + 1,
        )
        games.append(game)
    return games


def create_pgn_with_n_games(n: int) -> str:
    """Create PGN content with N games."""
    games = []
    for i in range(n):
        game = f'''[Event "Game {i+1}"]
[White "Player"]
[Black "Opponent"]
[Result "*"]

1. e4 e5 *
'''
        games.append(game)
    return "\n".join(games)


def test_detect_chapters_single_study():
    """Test detection with <= 64 chapters (single study)."""
    pgn = create_pgn_with_n_games(30)
    result = detect_chapters(pgn)

    assert result.total_chapters == 30
    assert result.requires_split is False
    assert result.is_single_study is True
    assert result.num_studies == 1
    assert result.chapters_per_study == [30]


def test_detect_chapters_exactly_64():
    """Test detection with exactly 64 chapters (edge case)."""
    pgn = create_pgn_with_n_games(64)
    result = detect_chapters(pgn)

    assert result.total_chapters == 64
    assert result.requires_split is False
    assert result.num_studies == 1
    assert result.chapters_per_study == [64]


def test_detect_chapters_requires_split():
    """Test detection with > 64 chapters (needs split)."""
    pgn = create_pgn_with_n_games(100)
    result = detect_chapters(pgn)

    assert result.total_chapters == 100
    assert result.requires_split is True
    assert result.is_single_study is False
    assert result.num_studies == 2
    assert sum(result.chapters_per_study) == 100
    # Should be roughly balanced
    assert all(c <= MAX_CHAPTERS_PER_STUDY for c in result.chapters_per_study)


def test_detect_chapters_large_split():
    """Test detection with many chapters requiring multiple studies."""
    pgn = create_pgn_with_n_games(200)
    result = detect_chapters(pgn)

    assert result.total_chapters == 200
    assert result.requires_split is True
    assert result.num_studies == 4  # ceil(200/64) = 4
    assert sum(result.chapters_per_study) == 200


def test_calculate_split_distribution_even():
    """Test even distribution of chapters."""
    # 100 chapters into 2 studies: [50, 50]
    dist = calculate_split_distribution(100, 2)
    assert dist == [50, 50]


def test_calculate_split_distribution_uneven():
    """Test uneven distribution (with remainder)."""
    # 130 chapters into 3 studies
    dist = calculate_split_distribution(130, 3)
    assert dist == [44, 43, 43]
    assert sum(dist) == 130


def test_calculate_split_distribution_many_studies():
    """Test distribution across many studies."""
    # 300 chapters into 5 studies: [60, 60, 60, 60, 60]
    dist = calculate_split_distribution(300, 5)
    assert dist == [60, 60, 60, 60, 60]


def test_split_games_into_studies():
    """Test splitting game list into studies."""
    games = create_mock_games(100)
    distribution = [50, 50]

    studies = split_games_into_studies(games, distribution)

    assert len(studies) == 2
    assert len(studies[0]) == 50
    assert len(studies[1]) == 50

    # Check ordering preserved
    assert studies[0][0].game_number == 1
    assert studies[0][49].game_number == 50
    assert studies[1][0].game_number == 51
    assert studies[1][49].game_number == 100


def test_split_games_uneven():
    """Test splitting with uneven distribution."""
    games = create_mock_games(130)
    distribution = [44, 43, 43]

    studies = split_games_into_studies(games, distribution)

    assert len(studies) == 3
    assert len(studies[0]) == 44
    assert len(studies[1]) == 43
    assert len(studies[2]) == 43


def test_suggest_study_names_single():
    """Test study name suggestion for single study."""
    names = suggest_study_names("Sicilian Defense", 1, [50])
    assert names == ["Sicilian Defense"]


def test_suggest_study_names_split():
    """Test study name suggestion for split studies."""
    names = suggest_study_names("Sicilian Defense", 3, [44, 43, 43])

    assert len(names) == 3
    assert "Part 1" in names[0]
    assert "Part 2" in names[1]
    assert "Part 3" in names[2]

    # Check chapter ranges
    assert "ch. 1-44" in names[0]
    assert "ch. 45-87" in names[1]
    assert "ch. 88-130" in names[2]


def test_suggest_study_names_two_parts():
    """Test study name suggestion for two-part split."""
    names = suggest_study_names("Opening Repertoire", 2, [50, 50])

    assert len(names) == 2
    assert names[0] == "Opening Repertoire - Part 1 (ch. 1-50)"
    assert names[1] == "Opening Repertoire - Part 2 (ch. 51-100)"


def test_detect_chapters_fast_vs_slow():
    """Test that fast and slow detection give same result."""
    pgn = create_pgn_with_n_games(75)

    result_fast = detect_chapters(pgn, fast=True)
    result_slow = detect_chapters(pgn, fast=False)

    assert result_fast.total_chapters == result_slow.total_chapters
    assert result_fast.requires_split == result_slow.requires_split
    assert result_fast.num_studies == result_slow.num_studies


def test_max_chapters_constant():
    """Test that MAX_CHAPTERS_PER_STUDY is 64."""
    assert MAX_CHAPTERS_PER_STUDY == 64
