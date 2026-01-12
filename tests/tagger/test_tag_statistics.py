"""
Tests for tag statistics collection and calculation.
"""

import pytest

from backend.core.tagger.analysis.tag_statistics import TagStatistics
from backend.core.tagger.tag_result import TagResult


class TestTagStatistics:
    """Test tag statistics functionality."""

    def test_empty_statistics(self):
        """Test statistics with no data."""
        stats = TagStatistics()
        assert stats.total_positions == 0
        assert len(stats.tag_counts) == 0
        assert stats.get_percentages() == {}

    def test_add_single_result(self):
        """Test adding a single tag result."""
        stats = TagStatistics()

        result = TagResult(
            played_move="e2e4",
            played_kind="quiet",
            best_move="e2e4",
            best_kind="quiet",
            eval_before=0.0,
            eval_played=0.0,
            eval_best=0.0,
            delta_eval=0.0,
            first_choice=True,
            tactical_sensitivity=False,
        )

        stats.add_result(result)

        assert stats.total_positions == 1
        assert stats.tag_counts["first_choice"] == 1
        assert "tactical_sensitivity" not in stats.tag_counts

    def test_multiple_results(self):
        """Test adding multiple results."""
        stats = TagStatistics()

        # Add 3 results with different tags
        for i in range(3):
            result = TagResult(
                played_move="e2e4",
                played_kind="quiet",
                best_move="e2e4",
                best_kind="quiet",
                eval_before=0.0,
                eval_played=0.0,
                eval_best=0.0,
                delta_eval=0.0,
                first_choice=(i < 2),  # True for first 2
                missed_tactic=(i == 1),  # True for second only
            )
            stats.add_result(result)

        assert stats.total_positions == 3
        assert stats.tag_counts["first_choice"] == 2
        assert stats.tag_counts["missed_tactic"] == 1

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        stats = TagStatistics()

        # Add 4 results
        for i in range(4):
            result = TagResult(
                played_move="e2e4",
                played_kind="quiet",
                best_move="e2e4",
                best_kind="quiet",
                eval_before=0.0,
                eval_played=0.0,
                eval_best=0.0,
                delta_eval=0.0,
                first_choice=(i < 3),  # 3 out of 4 = 75%
                tactical_sensitivity=(i < 2),  # 2 out of 4 = 50%
            )
            stats.add_result(result)

        percentages = stats.get_percentages()
        assert percentages["first_choice"] == 75.0
        assert percentages["tactical_sensitivity"] == 50.0

    def test_sorted_percentages(self):
        """Test sorted percentage output."""
        stats = TagStatistics()

        for i in range(10):
            result = TagResult(
                played_move="e2e4",
                played_kind="quiet",
                best_move="e2e4",
                best_kind="quiet",
                eval_before=0.0,
                eval_played=0.0,
                eval_best=0.0,
                delta_eval=0.0,
                first_choice=(i < 8),  # 80%
                missed_tactic=(i < 3),  # 30%
                tactical_sensitivity=(i < 5),  # 50%
            )
            stats.add_result(result)

        sorted_pcts = stats.get_sorted_percentages()

        # Should be sorted descending by percentage
        assert len(sorted_pcts) == 3
        assert sorted_pcts[0][0] == "first_choice"
        assert sorted_pcts[0][1] == 80.0
        assert sorted_pcts[0][2] == 8
        assert sorted_pcts[1][0] == "tactical_sensitivity"
        assert sorted_pcts[1][1] == 50.0

    def test_format_report(self):
        """Test report formatting."""
        stats = TagStatistics()

        result = TagResult(
            played_move="e2e4",
            played_kind="quiet",
            best_move="e2e4",
            best_kind="quiet",
            eval_before=0.0,
            eval_played=0.0,
            eval_best=0.0,
            delta_eval=0.0,
            first_choice=True,
        )
        stats.add_result(result)

        report = stats.format_report()

        assert "TAG STATISTICS REPORT" in report
        assert "Total Positions Analyzed: 1" in report
        assert "first_choice" in report
        assert "100.00%" in report
