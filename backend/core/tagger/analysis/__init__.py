"""
PGN Analysis Pipeline for Tag Statistics.

This package provides tools to analyze PGN files and calculate
tag occurrence percentages across games.
"""

from .pipeline import AnalysisPipeline
from .tag_statistics import TagStatistics

__all__ = ["AnalysisPipeline", "TagStatistics"]
