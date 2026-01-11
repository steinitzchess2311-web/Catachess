"""
Standalone tests for prophylaxis helpers (no backend dependencies).

Run with: python3 -m pytest tests/test_prophylaxis_standalone.py -v
"""
import sys
from pathlib import Path
from dataclasses import FrozenInstanceError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from core.tagger.detectors.helpers.prophylaxis import (
    ProphylaxisConfig,
    clamp_preventive_score,
    is_full_material,
)


class TestProphylaxisConfigDefaults:
    """Test default configuration values."""

    def test_all_defaults_match_rule_tagger2(self):
        """All default values should match rule_tagger2 exactly."""
        cfg = ProphylaxisConfig()
        assert cfg.structure_min == 0.2
        assert cfg.opp_mobility_drop == 0.15
        assert cfg.self_mobility_tol == 0.3
        assert cfg.preventive_trigger == 0.16
        assert cfg.safety_cap == 0.6
        assert cfg.score_threshold == 0.20
        assert cfg.threat_depth == 6
        assert cfg.threat_drop == 0.35


class TestProphylaxisConfigImmutability:
    """Test that config is immutable (frozen)."""

    def test_cannot_modify_after_creation(self):
        """Cannot modify any field after creation."""
        cfg = ProphylaxisConfig()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            cfg.preventive_trigger = 0.25


class TestProphylaxisConfigCustomValues:
    """Test custom initialization."""

    def test_custom_values_work(self):
        """Can set custom values during initialization."""
        cfg = ProphylaxisConfig(
            preventive_trigger=0.25,
            safety_cap=0.5,
            threat_depth=10
        )
        assert cfg.preventive_trigger == 0.25
        assert cfg.safety_cap == 0.5
        assert cfg.threat_depth == 10
        # Others remain default
        assert cfg.structure_min == 0.2


class TestClampPreventiveScore:
    """Test clamp_preventive_score function."""

    def test_negative_scores_clamp_to_zero(self):
        """Negative scores should clamp to 0.0."""
        cfg = ProphylaxisConfig()
        assert clamp_preventive_score(-0.5, config=cfg) == 0.0
        assert clamp_preventive_score(-10.0, config=cfg) == 0.0

    def test_zero_unchanged(self):
        """Zero should remain 0.0."""
        cfg = ProphylaxisConfig()
        assert clamp_preventive_score(0.0, config=cfg) == 0.0

    def test_within_cap_unchanged(self):
        """Scores within cap should be unchanged."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        assert clamp_preventive_score(0.3, config=cfg) == 0.3
        assert clamp_preventive_score(0.59, config=cfg) == 0.59

    def test_above_cap_clamped(self):
        """Scores above cap should clamp to cap."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        assert clamp_preventive_score(0.8, config=cfg) == 0.6
        assert clamp_preventive_score(10.0, config=cfg) == 0.6

    def test_at_cap_unchanged(self):
        """Score exactly at cap should remain at cap."""
        cfg = ProphylaxisConfig(safety_cap=0.6)
        assert clamp_preventive_score(0.6, config=cfg) == 0.6

    def test_custom_cap(self):
        """Custom safety_cap should work."""
        cfg = ProphylaxisConfig(safety_cap=0.4)
        assert clamp_preventive_score(0.5, config=cfg) == 0.4
        assert clamp_preventive_score(0.3, config=cfg) == 0.3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
