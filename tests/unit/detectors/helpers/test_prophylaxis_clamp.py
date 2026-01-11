"""
Test clamp_preventive_score function.

Tests verify clamping behavior matches rule_tagger2 exactly.
"""
import pytest

from backend.core.tagger.detectors.helpers.prophylaxis import (
    ProphylaxisConfig,
    clamp_preventive_score,
)


class TestClampNegativeScores:
    """Test clamping of negative scores."""

    def test_negative_score_becomes_zero(self):
        """Negative scores should clamp to 0.0."""
        cfg = ProphylaxisConfig()
        result = clamp_preventive_score(-0.5, config=cfg)
        assert result == 0.0

    def test_large_negative_score(self):
        """Large negative scores should clamp to 0.0."""
        cfg = ProphylaxisConfig()
        result = clamp_preventive_score(-10.0, config=cfg)
        assert result == 0.0


class TestClampZeroScore:
    """Test clamping of zero score."""

    def test_zero_score_unchanged(self):
        """Zero should remain 0.0."""
        cfg = ProphylaxisConfig()
        result = clamp_preventive_score(0.0, config=cfg)
        assert result == 0.0


class TestClampWithinCap:
    """Test scores within safety_cap."""

    def test_small_positive_score(self):
        """Small positive scores should be unchanged."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        result = clamp_preventive_score(0.3, config=cfg)
        assert result == 0.3

    def test_score_just_below_cap(self):
        """Score just below cap should be unchanged."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        result = clamp_preventive_score(0.59, config=cfg)
        assert result == 0.59


class TestClampAboveCap:
    """Test scores above safety_cap."""

    def test_score_above_cap_clamped(self):
        """Scores above cap should clamp to cap."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        result = clamp_preventive_score(0.8, config=cfg)
        assert result == 0.6

    def test_large_score_clamped(self):
        """Very large scores should clamp to cap."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        result = clamp_preventive_score(10.0, config=cfg)
        assert result == 0.6


class TestClampAtCap:
    """Test score exactly at cap."""

    def test_score_at_cap_unchanged(self):
        """Score exactly at cap should remain at cap."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        result = clamp_preventive_score(0.6, config=cfg)
        assert result == 0.6


class TestClampCustomCap:
    """Test with custom safety_cap values."""

    def test_custom_cap_above(self):
        """Score above custom cap should clamp."""
        cfg = ProphylaxisConfig(safety_cap=0.4)
        result = clamp_preventive_score(0.5, config=cfg)
        assert result == 0.4

    def test_custom_cap_below(self):
        """Score below custom cap should be unchanged."""
        cfg = ProphylaxisConfig(safety_cap=0.8)
        result = clamp_preventive_score(0.5, config=cfg)
        assert result == 0.5

    def test_custom_cap_at_boundary(self):
        """Score at custom cap should be unchanged."""
        cfg = ProphylaxisConfig(safety_cap=0.5)
        result = clamp_preventive_score(0.5, config=cfg)
        assert result == 0.5


class TestClampEdgeCases:
    """Test edge cases."""

    def test_very_small_positive_score(self):
        """Very small positive scores should be unchanged."""
        cfg = ProphylaxisConfig()
        result = clamp_preventive_score(0.001, config=cfg)
        assert result == 0.001

    def test_score_slightly_negative(self):
        """Slightly negative scores should clamp to 0.0."""
        cfg = ProphylaxisConfig()
        result = clamp_preventive_score(-0.001, config=cfg)
        assert result == 0.0
