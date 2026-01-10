"""
Base class for tag detectors.
Each tag detector must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..models import TagContext, TagEvidence


class TagDetector(ABC):
    """
    Base class for all tag detectors.

    Each detector is responsible for detecting a single tag or a small
    family of related tags. Detectors must be stateless and only depend
    on the TagContext provided.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the detector name."""
        ...

    @property
    @abstractmethod
    def tags(self) -> list[str]:
        """Return list of tag names this detector can produce."""
        ...

    @abstractmethod
    def detect(self, ctx: TagContext) -> list[TagEvidence]:
        """
        Detect tags based on the context.

        Args:
            ctx: Read-only tag context with all analysis data

        Returns:
            List of TagEvidence objects (can be empty if no tags fire)
        """
        ...

    def is_applicable(self, ctx: TagContext) -> bool:
        """
        Check if detector is applicable for this context.

        Override this to skip detection in certain positions
        (e.g., endgame-only detectors).

        Args:
            ctx: Tag context

        Returns:
            True if detector should run
        """
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Return detector metadata.

        Returns:
            Dictionary with version, description, etc.
        """
        return {
            "name": self.name,
            "tags": self.tags,
            "version": "1.0",
        }


__all__ = ["TagDetector"]
