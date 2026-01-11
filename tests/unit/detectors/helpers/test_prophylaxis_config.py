"""
Test ProphylaxisConfig dataclass.

Tests verify that configuration values match rule_tagger2 exactly.
"""
import pytest
from dataclasses import FrozenInstanceError

from backend.core.tagger.detectors.helpers.prophylaxis import ProphylaxisConfig


class TestProphylaxisConfigDefaults:
    """Test default configuration values."""

    def test_default_structure_min(self):
        """structure_min should default to 0.2."""
        cfg = ProphylaxisConfig()
        assert cfg.structure_min == 0.2

    def test_default_opp_mobility_drop(self):
        """opp_mobility_drop should default to 0.15."""
        cfg = ProphylaxisConfig()
        assert cfg.opp_mobility_drop == 0.15

    def test_default_self_mobility_tol(self):
        """self_mobility_tol should default to 0.3."""
        cfg = ProphylaxisConfig()
        assert cfg.self_mobility_tol == 0.3

    def test_default_preventive_trigger(self):
        """preventive_trigger should default to 0.16."""
        cfg = ProphylaxisConfig()
        assert cfg.preventive_trigger == 0.16

    def test_default_safety_cap(self):
        """safety_cap should default to 0.6."""
        cfg = ProphylaxisConfig()
        assert cfg.safety_cap == 0.6

    def test_default_score_threshold(self):
        """score_threshold should default to 0.20."""
        cfg = ProphylaxisConfig()
        assert cfg.score_threshold == 0.20

    def test_default_threat_depth(self):
        """threat_depth should default to 6."""
        cfg = ProphylaxisConfig()
        assert cfg.threat_depth == 6

    def test_default_threat_drop(self):
        """threat_drop should default to 0.35."""
        cfg = ProphylaxisConfig()
        assert cfg.threat_drop == 0.35


class TestProphylaxisConfigImmutability:
    """Test that config is immutable (frozen)."""

    def test_frozen_structure_min(self):
        """Cannot modify structure_min after creation."""
        cfg = ProphylaxisConfig()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            cfg.structure_min = 0.5

    def test_frozen_preventive_trigger(self):
        """Cannot modify preventive_trigger after creation."""
        cfg = ProphylaxisConfig()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            cfg.preventive_trigger = 0.25

    def test_frozen_threat_depth(self):
        """Cannot modify threat_depth after creation."""
        cfg = ProphylaxisConfig()
        with pytest.raises((FrozenInstanceError, AttributeError)):
            cfg.threat_depth = 10


class TestProphylaxisConfigCustomValues:
    """Test custom initialization."""

    def test_custom_preventive_trigger(self):
        """Can set custom preventive_trigger."""
        cfg = ProphylaxisConfig(preventive_trigger=0.25)
        assert cfg.preventive_trigger == 0.25
        # Other values remain default
        assert cfg.structure_min == 0.2

    def test_custom_threat_depth(self):
        """Can set custom threat_depth."""
        cfg = ProphylaxisConfig(threat_depth=8)
        assert cfg.threat_depth == 8
        # Other values remain default
        assert cfg.opp_mobility_drop == 0.15

    def test_multiple_custom_values(self):
        """Can set multiple custom values."""
        cfg = ProphylaxisConfig(
            preventive_trigger=0.20,
            safety_cap=0.5,
            threat_depth=10
        )
        assert cfg.preventive_trigger == 0.20
        assert cfg.safety_cap == 0.5
        assert cfg.threat_depth == 10
        # Others remain default
        assert cfg.structure_min == 0.2


class TestProphylaxisConfigEquality:
    """Test config equality."""

    def test_equal_default_configs(self):
        """Two default configs should be equal."""
        cfg1 = ProphylaxisConfig()
        cfg2 = ProphylaxisConfig()
        assert cfg1 == cfg2

    def test_equal_custom_configs(self):
        """Two configs with same custom values should be equal."""
        cfg1 = ProphylaxisConfig(preventive_trigger=0.25)
        cfg2 = ProphylaxisConfig(preventive_trigger=0.25)
        assert cfg1 == cfg2

    def test_unequal_configs(self):
        """Configs with different values should not be equal."""
        cfg1 = ProphylaxisConfig(preventive_trigger=0.16)
        cfg2 = ProphylaxisConfig(preventive_trigger=0.25)
        assert cfg1 != cfg2
