"""
Tag statistics collection and calculation.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from ..tag_result import TagResult


@dataclass
class TagStatistics:
    """Collects and calculates statistics on tag occurrences."""

    total_positions: int = 0
    tag_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add_result(self, result: TagResult) -> None:
        """
        Add a tagging result to statistics.

        Args:
            result: TagResult from pipeline
        """
        self.total_positions += 1

        # Iterate through all boolean tag fields
        for field_name in dir(result):
            # Skip private/magic attributes and non-tag fields
            if field_name.startswith('_'):
                continue
            if field_name in ['played_move', 'played_kind', 'best_move', 'best_kind',
                            'eval_before', 'eval_played', 'eval_best', 'delta_eval',
                            'metrics_before', 'metrics_played', 'metrics_best',
                            'component_deltas', 'opp_metrics_before', 'opp_metrics_played',
                            'opp_metrics_best', 'opp_component_deltas', 'coverage_delta',
                            'tactical_weight', 'mode', 'analysis_context', 'notes',
                            'control_over_dynamics_subtype', 'prophylaxis_score',
                            'maneuver_precision_score', 'maneuver_timing_score',
                            'prepare_quality_score', 'prepare_consensus_score',
                            'control_schema_version']:
                continue

            value = getattr(result, field_name, None)
            if isinstance(value, bool) and value:
                self.tag_counts[field_name] += 1

    def get_percentages(self) -> Dict[str, float]:
        """
        Calculate percentage for each tag.

        Returns:
            Dictionary mapping tag name to percentage (0-100)
        """
        if self.total_positions == 0:
            return {}

        percentages = {}
        for tag, count in self.tag_counts.items():
            percentages[tag] = (count / self.total_positions) * 100

        return percentages

    def get_sorted_percentages(self) -> List[tuple[str, float, int]]:
        """
        Get sorted list of tags by percentage (descending).

        Returns:
            List of tuples (tag_name, percentage, count)
        """
        percentages = self.get_percentages()
        return sorted(
            [(tag, pct, self.tag_counts[tag]) for tag, pct in percentages.items()],
            key=lambda x: x[1],
            reverse=True
        )

    def format_report(self) -> str:
        """
        Generate a formatted text report of tag statistics.

        Returns:
            Formatted report string
        """
        lines = [
            "=" * 80,
            "TAG STATISTICS REPORT",
            "=" * 80,
            f"Total Positions Analyzed: {self.total_positions}",
            "",
            "Tag Occurrences (sorted by frequency):",
            "-" * 80,
            f"{'Tag Name':<50} {'Count':>10} {'Percentage':>15}",
            "-" * 80,
        ]

        for tag_name, percentage, count in self.get_sorted_percentages():
            lines.append(f"{tag_name:<50} {count:>10} {percentage:>14.2f}%")

        lines.extend([
            "-" * 80,
            f"Total unique tags found: {len(self.tag_counts)}",
            "=" * 80,
        ])

        return "\n".join(lines)


__all__ = ["TagStatistics"]
