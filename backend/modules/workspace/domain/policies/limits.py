"""
System limits and constraints.

These limits define the boundaries of the system to ensure
performance, usability, and data integrity.
"""


class StudyLimits:
    """
    Limits for Study objects.

    The 64-chapter limit is a key architectural decision:
    - Prevents single study from becoming too large
    - Ensures reasonable UI performance
    - Automatically splits large imports into manageable pieces
    """

    # Maximum chapters per study (chess board = 64 squares, memorable number)
    MAX_CHAPTERS_PER_STUDY = 64

    # Maximum variations per move (prevent exponential tree growth)
    MAX_VARIATIONS_PER_MOVE = 10

    # Maximum annotation length (characters)
    MAX_ANNOTATION_LENGTH = 10000

    # Maximum chapter title length
    MAX_CHAPTER_TITLE_LENGTH = 200


class DiscussionLimits:
    """
    Limits for discussion/comment system.

    Nested reply limits prevent UI complexity and improve readability.
    """

    # Maximum nesting level for replies (3-5 is typical)
    MAX_REPLY_NESTING_LEVEL = 5

    # Maximum discussion thread title length
    MAX_THREAD_TITLE_LENGTH = 200

    # Maximum reply content length
    MAX_REPLY_LENGTH = 10000

    # Maximum reactions per comment
    MAX_REACTIONS_PER_COMMENT = 100

    # Allowed reaction emojis
    ALLOWED_REACTION_EMOJIS = {"👍", "❤️", "🎯"}


class NodeLimits:
    """
    Limits for node tree operations.

    While folders can nest infinitely, we set practical limits
    for UI display and performance.
    """

    # Maximum folder nesting depth (for UI display recommendation)
    # Backend supports infinite nesting, but UI should limit display
    RECOMMENDED_MAX_FOLDER_DEPTH = 10

    # Maximum node title length
    MAX_NODE_TITLE_LENGTH = 200

    # Maximum description length
    MAX_DESCRIPTION_LENGTH = 5000


class NotificationLimits:
    """
    Limits for notification system.
    """

    # Maximum notifications to fetch per page
    MAX_NOTIFICATIONS_PER_PAGE = 50

    # Maximum notification retention days
    NOTIFICATION_RETENTION_DAYS = 90

    # Maximum batch size for bulk operations
    MAX_BULK_OPERATION_SIZE = 100


class PresenceLimits:
    """
    Limits for presence/collaboration system.
    """

    # Heartbeat timeout (seconds)
    # No heartbeat for 30s → IDLE
    HEARTBEAT_IDLE_TIMEOUT = 30

    # Away timeout (seconds)
    # No heartbeat for 5min → AWAY
    HEARTBEAT_AWAY_TIMEOUT = 300

    # Session cleanup timeout (seconds)
    # No heartbeat for 30min → cleanup session
    SESSION_CLEANUP_TIMEOUT = 1800


class ExportLimits:
    """
    Limits for export operations.
    """

    # Maximum concurrent export jobs per user
    MAX_CONCURRENT_EXPORTS_PER_USER = 3

    # Export job timeout (seconds)
    EXPORT_JOB_TIMEOUT = 600  # 10 minutes

    # Maximum export size (MB)
    MAX_EXPORT_SIZE_MB = 500


# Chapter splitting strategy
class ChapterSplitStrategy:
    """
    Strategy for handling PGN imports with > 64 chapters.

    When a PGN contains more than MAX_CHAPTERS_PER_STUDY chapters,
    the system automatically:
    1. Creates a folder (user provides base_name)
    2. Creates multiple studies: {base_name}_1, {base_name}_2, ...
    3. Each study contains up to MAX_CHAPTERS_PER_STUDY chapters
    """

    @staticmethod
    def calculate_required_studies(chapter_count: int) -> int:
        """
        Calculate how many studies are needed to hold all chapters.

        Args:
            chapter_count: Total number of chapters

        Returns:
            Number of studies needed
        """
        return (chapter_count + StudyLimits.MAX_CHAPTERS_PER_STUDY - 1) // StudyLimits.MAX_CHAPTERS_PER_STUDY

    @staticmethod
    def generate_study_name(base_name: str, index: int) -> str:
        """
        Generate study name for split import.

        Args:
            base_name: Base name provided by user
            index: Study index (1-based)

        Returns:
            Study name like: {base_name}_1, {base_name}_2, ...
        """
        return f"{base_name}_{index}"

    @staticmethod
    def needs_splitting(chapter_count: int) -> bool:
        """
        Check if chapter count requires splitting.

        Args:
            chapter_count: Total number of chapters

        Returns:
            True if > MAX_CHAPTERS_PER_STUDY
        """
        return chapter_count > StudyLimits.MAX_CHAPTERS_PER_STUDY
