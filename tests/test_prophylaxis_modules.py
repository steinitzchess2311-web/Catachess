"""
Test split prophylaxis modules (each file < 100 lines).

Run with: python3 tests/test_prophylaxis_modules.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.tagger.detectors.helpers.prophylaxis_modules import (
    ProphylaxisConfig,
    clamp_preventive_score,
    classify_prophylaxis_quality,
)


def test_config_defaults():
    """Test ProphylaxisConfig defaults match rule_tagger2."""
    cfg = ProphylaxisConfig()
    assert cfg.structure_min == 0.2
    assert cfg.opp_mobility_drop == 0.15
    assert cfg.self_mobility_tol == 0.3
    assert cfg.preventive_trigger == 0.16
    assert cfg.safety_cap == 0.6
    assert cfg.score_threshold == 0.20
    assert cfg.threat_depth == 6
    assert cfg.threat_drop == 0.35
    print("✓ test_config_defaults")


def test_config_immutable():
    """Test config is frozen."""
    cfg = ProphylaxisConfig()
    try:
        cfg.preventive_trigger = 0.25
        assert False, "Should not be able to modify frozen config"
    except Exception:
        pass
    print("✓ test_config_immutable")


def test_config_custom():
    """Test custom config values."""
    cfg = ProphylaxisConfig(preventive_trigger=0.25, threat_depth=10)
    assert cfg.preventive_trigger == 0.25
    assert cfg.threat_depth == 10
    assert cfg.structure_min == 0.2  # default unchanged
    print("✓ test_config_custom")


def test_clamp_negative():
    """Test clamping negative scores."""
    cfg = ProphylaxisConfig()
    assert clamp_preventive_score(-0.5, config=cfg) == 0.0
    assert clamp_preventive_score(-10.0, config=cfg) == 0.0
    print("✓ test_clamp_negative")


def test_clamp_zero():
    """Test zero unchanged."""
    cfg = ProphylaxisConfig()
    assert clamp_preventive_score(0.0, config=cfg) == 0.0
    print("✓ test_clamp_zero")


def test_clamp_within_cap():
    """Test scores within cap unchanged."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.3, config=cfg) == 0.3
    assert clamp_preventive_score(0.59, config=cfg) == 0.59
    print("✓ test_clamp_within_cap")


def test_clamp_above_cap():
    """Test scores above cap are clamped."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.8, config=cfg) == 0.6
    assert clamp_preventive_score(10.0, config=cfg) == 0.6
    print("✓ test_clamp_above_cap")


def test_clamp_at_cap():
    """Test score at cap unchanged."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.6, config=cfg) == 0.6
    print("✓ test_clamp_at_cap")


def test_classify_no_prophylaxis():
    """Test classification with no prophylaxis."""
    cfg = ProphylaxisConfig()
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=False,
        preventive_score=0.3,
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.5,
        config=cfg
    )
    assert label is None
    assert score == 0.0
    print("✓ test_classify_no_prophylaxis")


def test_classify_failure():
    """Test failure case (eval drop in neutral position)."""
    cfg = ProphylaxisConfig()
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.3,
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.5,
        eval_before_cp=50,
        drop_cp=-80,
        config=cfg
    )
    assert label == "prophylactic_meaningless"
    assert score == 0.0
    print("✓ test_classify_failure")


def test_classify_direct():
    """Test direct classification."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.20,  # >= trigger + 0.02
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.5,
        config=cfg
    )
    assert label == "prophylactic_direct"
    assert score >= 0.20  # at least score_threshold
    assert score <= 0.6   # capped at safety_cap
    print("✓ test_classify_direct")


def test_classify_latent():
    """Test latent classification."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.17,  # above trigger but no direct_gate
        effective_delta=-0.1,
        tactical_weight=0.7,
        soft_weight=0.4,
        config=cfg
    )
    assert label == "prophylactic_latent"
    assert score >= 0.45  # at least latent base for negative delta would be 0.55
    print("✓ test_classify_latent")


def test_classify_pattern_override():
    """Test pattern override with meaningful signal."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.12,  # below trigger
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.35,  # >= 0.3 (meaningful signal)
        pattern_override=True,
        config=cfg
    )
    assert label == "prophylactic_latent"
    assert score > 0.0
    print("✓ test_classify_pattern_override")


def test_classify_below_trigger_no_pattern():
    """Test below trigger without pattern override."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.12,
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.4,
        pattern_override=False,
        config=cfg
    )
    assert label is None
    assert score == 0.0
    print("✓ test_classify_below_trigger_no_pattern")


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("Testing split prophylaxis modules (each file < 100 lines)")
    print("=" * 70)

    tests = [
        test_config_defaults,
        test_config_immutable,
        test_config_custom,
        test_clamp_negative,
        test_clamp_zero,
        test_clamp_within_cap,
        test_clamp_above_cap,
        test_clamp_at_cap,
        test_classify_no_prophylaxis,
        test_classify_failure,
        test_classify_direct,
        test_classify_latent,
        test_classify_pattern_override,
        test_classify_below_trigger_no_pattern,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1

    print("=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n❌ {failed} tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
