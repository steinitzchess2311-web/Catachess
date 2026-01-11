"""
Chapter detection and study splitting logic.

Detects number of chapters (games) in PGN and determines
if splitting into multiple studies is needed.
"""

from dataclasses import dataclass

from .parser.split_games import count_games, split_games, PGNGame


# Maximum chapters per study (Lichess limit)
MAX_CHAPTERS_PER_STUDY = 64


@dataclass
class ChapterDetectionResult:
    """
    Result of chapter detection.

    Attributes:
        total_chapters: Total number of chapters (games) in PGN
        requires_split: Whether PGN exceeds 64-chapter limit
        num_studies: Number of studies needed
        chapters_per_study: List of chapter counts per study
    """

    total_chapters: int
    requires_split: bool
    num_studies: int
    chapters_per_study: list[int]

    @property
    def is_single_study(self) -> bool:
        """Check if PGN fits in single study."""
        return not self.requires_split


def detect_chapters(pgn_content: str, fast: bool = True) -> ChapterDetectionResult:
    """
    Detect number of chapters in PGN and determine split strategy.

    Args:
        pgn_content: Normalized PGN content
        fast: Use fast counting (default True). If False, fully parse games.

    Returns:
        ChapterDetectionResult with split strategy
    """
    # Count total chapters
    if fast:
        total = count_games(pgn_content)
    else:
        games = split_games(pgn_content)
        total = len(games)

    # Determine if split needed
    requires_split = total > MAX_CHAPTERS_PER_STUDY

    if not requires_split:
        # Single study
        return ChapterDetectionResult(
            total_chapters=total,
            requires_split=False,
            num_studies=1,
            chapters_per_study=[total],
        )

    # Split needed - calculate distribution
    num_studies = (total + MAX_CHAPTERS_PER_STUDY - 1) // MAX_CHAPTERS_PER_STUDY
    chapters_per_study = calculate_split_distribution(total, num_studies)

    return ChapterDetectionResult(
        total_chapters=total,
        requires_split=True,
        num_studies=num_studies,
        chapters_per_study=chapters_per_study,
    )


def calculate_split_distribution(total_chapters: int, num_studies: int) -> list[int]:
    """
    Calculate optimal distribution of chapters across studies.

    Tries to balance chapters evenly across studies.

    Example:
        total=100, num_studies=2 -> [50, 50]
        total=130, num_studies=3 -> [44, 43, 43]

    Args:
        total_chapters: Total number of chapters
        num_studies: Number of studies to split into

    Returns:
        List of chapter counts per study
    """
    base_count = total_chapters // num_studies
    remainder = total_chapters % num_studies

    distribution = []
    for i in range(num_studies):
        # First 'remainder' studies get one extra chapter
        count = base_count + (1 if i < remainder else 0)
        distribution.append(count)

    return distribution


def split_games_into_studies(
    games: list[PGNGame],
    distribution: list[int],
) -> list[list[PGNGame]]:
    """
    Split list of games into studies according to distribution.

    Args:
        games: List of all games
        distribution: Number of chapters per study

    Returns:
        List of game lists (one per study)
    """
    studies = []
    offset = 0

    for count in distribution:
        study_games = games[offset : offset + count]
        studies.append(study_games)
        offset += count

    return studies


def suggest_study_names(
    base_name: str,
    num_studies: int,
    distribution: list[int],
) -> list[str]:
    """
    Generate suggested study names for split studies.

    Examples:
        base_name="Sicilian Defense", num_studies=3
        -> ["Sicilian Defense - Part 1 (1-50)",
            "Sicilian Defense - Part 2 (51-100)",
            "Sicilian Defense - Part 3 (101-130)"]

    Args:
        base_name: Base study name
        num_studies: Number of studies
        distribution: Chapters per study

    Returns:
        List of suggested study names
    """
    if num_studies == 1:
        return [base_name]

    names = []
    offset = 1  # 1-based chapter numbering

    for i, count in enumerate(distribution, 1):
        start = offset
        end = offset + count - 1
        name = f"{base_name} - Part {i} (ch. {start}-{end})"
        names.append(name)
        offset = end + 1

    return names
