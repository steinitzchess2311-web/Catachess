"""
R2 Key Naming Conventions.

These conventions define how objects are stored in Cloudflare R2 (S3-compatible).
DO NOT change these without a migration plan, as they affect existing data.

Key Structure:
- raw/{upload_id}.pgn          : Original uploaded PGN files (optional retention)
- chapters/{chapter_id}.pgn    : Normalized chapter PGN files
- exports/{job_id}.{pgn|zip}   : Export artifacts
- snapshots/{study_id}/{version}.json : Version snapshots
"""

from typing import Literal


class R2KeyPrefix:
    """R2 key prefixes for different object types."""
    RAW = "raw"
    CHAPTERS = "chapters"
    EXPORTS = "exports"
    SNAPSHOTS = "snapshots"


class R2Keys:
    """
    R2 key generator following naming conventions.

    All keys follow a consistent pattern to enable:
    - Easy listing by prefix
    - Clear separation by type
    - Predictable access patterns
    """

    @staticmethod
    def raw_upload(upload_id: str) -> str:
        """
        Generate key for raw uploaded PGN.

        Args:
            upload_id: Unique upload identifier

        Returns:
            Key like: raw/abc123def456.pgn
        """
        return f"{R2KeyPrefix.RAW}/{upload_id}.pgn"

    @staticmethod
    def chapter_pgn(chapter_id: str) -> str:
        """
        Generate key for normalized chapter PGN.

        Args:
            chapter_id: Unique chapter identifier

        Returns:
            Key like: chapters/chapter_abc123.pgn
        """
        return f"{R2KeyPrefix.CHAPTERS}/{chapter_id}.pgn"

    @staticmethod
    def chapter_tree_json(chapter_id: str) -> str:
        """
        Generate key for chapter NodeTree JSON.

        Args:
            chapter_id: Unique chapter identifier

        Returns:
            Key like: chapters/chapter_abc123.tree.json
        """
        return f"{R2KeyPrefix.CHAPTERS}/{chapter_id}.tree.json"

    @staticmethod
    def chapter_fen_index_json(chapter_id: str) -> str:
        """
        Generate key for chapter FEN index JSON.

        Args:
            chapter_id: Unique chapter identifier

        Returns:
            Key like: chapters/chapter_abc123.fen_index.json
        """
        return f"{R2KeyPrefix.CHAPTERS}/{chapter_id}.fen_index.json"

    @staticmethod
    def chapter_tags_json(chapter_id: str) -> str:
        """
        Generate key for chapter tags JSON (tagger output).

        Args:
            chapter_id: Unique chapter identifier

        Returns:
            Key like: chapters/chapter_abc123.tags.json
        """
        return f"{R2KeyPrefix.CHAPTERS}/{chapter_id}.tags.json"

    @staticmethod
    def export_artifact(job_id: str, format: Literal["pgn", "zip"]) -> str:
        """
        Generate key for export artifact.

        Args:
            job_id: Export job identifier
            format: Export format (pgn or zip)

        Returns:
            Key like: exports/job_abc123.pgn or exports/job_abc123.zip
        """
        return f"{R2KeyPrefix.EXPORTS}/{job_id}.{format}"

    @staticmethod
    def version_snapshot(study_id: str, version: int) -> str:
        """
        Generate key for version snapshot.

        Args:
            study_id: Study identifier
            version: Version number

        Returns:
            Key like: snapshots/study_abc123/42.json
        """
        return f"{R2KeyPrefix.SNAPSHOTS}/{study_id}/{version}.json"

    @staticmethod
    def list_prefix_for_study_snapshots(study_id: str) -> str:
        """
        Generate prefix for listing all snapshots of a study.

        Args:
            study_id: Study identifier

        Returns:
            Prefix like: snapshots/study_abc123/
        """
        return f"{R2KeyPrefix.SNAPSHOTS}/{study_id}/"


# R2 Configuration Constants
class R2Config:
    """
    R2 storage configuration constants.

    These values define storage behavior and limits.
    """

    # Maximum upload size (100 MB for single PGN file)
    MAX_UPLOAD_SIZE_MB = 100

    # Presigned URL expiry (1 hour for downloads)
    PRESIGNED_URL_EXPIRY_SECONDS = 3600

    # Content-Type mappings
    CONTENT_TYPE_PGN = "application/x-chess-pgn"
    CONTENT_TYPE_ZIP = "application/zip"
    CONTENT_TYPE_JSON = "application/json"

    @staticmethod
    def get_content_type(format: Literal["pgn", "zip", "json"]) -> str:
        """Get MIME type for format."""
        mapping = {
            "pgn": R2Config.CONTENT_TYPE_PGN,
            "zip": R2Config.CONTENT_TYPE_ZIP,
            "json": R2Config.CONTENT_TYPE_JSON,
        }
        return mapping.get(format, "application/octet-stream")
