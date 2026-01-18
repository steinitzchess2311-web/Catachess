"""
Direct tests for prophylaxis module.
"""
from backend.core.tagger.detectors.helpers.prophylaxis import (
    ProphylaxisConfig,
    clamp_preventive_score,
    classify_prophylaxis_quality,
)

# Run tests
def test_prophylaxis_config_defaults():
    """Test ProphylaxisConfig default values."""
    cfg = ProphylaxisConfig()
    assert cfg.structure_min == 0.2, f"Expected 0.2, got {cfg.structure_min}"
    assert cfg.opp_mobility_drop == 0.15, f"Expected 0.15, got {cfg.opp_mobility_drop}"
    assert cfg.self_mobility_tol == 0.3, f"Expected 0.3, got {cfg.self_mobility_tol}"
    assert cfg.preventive_trigger == 0.16, f"Expected 0.16, got {cfg.preventive_trigger}"
    assert cfg.safety_cap == 0.6, f"Expected 0.6, got {cfg.safety_cap}"
    assert cfg.score_threshold == 0.20, f"Expected 0.20, got {cfg.score_threshold}"
    assert cfg.threat_depth == 6, f"Expected 6, got {cfg.threat_depth}"
    assert cfg.threat_drop == 0.35, f"Expected 0.35, got {cfg.threat_drop}"
    print("✓ test_prophylaxis_config_defaults PASSED")


def test_prophylaxis_config_immutable():
    """Test that ProphylaxisConfig is frozen."""
    cfg = ProphylaxisConfig()
    try:
        cfg.preventive_trigger = 0.25
        raise AssertionError("Config should be frozen!")
    except (Exception,):
        print("✓ test_prophylaxis_config_immutable PASSED")


def test_prophylaxis_config_custom_values():
    """Test custom initialization."""
    cfg = ProphylaxisConfig(preventive_trigger=0.25, threat_depth=10)
    assert cfg.preventive_trigger == 0.25
    assert cfg.threat_depth == 10
    assert cfg.structure_min == 0.2  # default unchanged
    print("✓ test_prophylaxis_config_custom_values PASSED")


def test_clamp_negative_scores():
    """Test clamping negative scores to 0.0."""
    cfg = ProphylaxisConfig()
    assert clamp_preventive_score(-0.5, config=cfg) == 0.0
    assert clamp_preventive_score(-10.0, config=cfg) == 0.0
    print("✓ test_clamp_negative_scores PASSED")


def test_clamp_zero():
    """Test that zero remains zero."""
    cfg = ProphylaxisConfig()
    assert clamp_preventive_score(0.0, config=cfg) == 0.0
    print("✓ test_clamp_zero PASSED")


def test_clamp_within_cap():
    """Test scores within cap are unchanged."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.3, config=cfg) == 0.3
    assert clamp_preventive_score(0.59, config=cfg) == 0.59
    print("✓ test_clamp_within_cap PASSED")


def test_clamp_above_cap():
    """Test scores above cap are clamped."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.8, config=cfg) == 0.6
    assert clamp_preventive_score(10.0, config=cfg) == 0.6
    print("✓ test_clamp_above_cap PASSED")


def test_clamp_at_cap():
    """Test score at cap is unchanged."""
    cfg = ProphylaxisConfig(safety_cap=0.6)
    assert clamp_preventive_score(0.6, config=cfg) == 0.6
    print("✓ test_clamp_at_cap PASSED")


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
    print("✓ test_classify_no_prophylaxis PASSED")


def test_classify_failure_case():
    """Test failure case (neutral position with eval drop)."""
    cfg = ProphylaxisConfig()
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.3,
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.5,
        eval_before_cp=50,  # within ±200
        drop_cp=-80,        # < -50
        config=cfg
    )
    assert label == "prophylactic_meaningless"
    assert score == 0.0
    print("✓ test_classify_failure_case PASSED")


def test_classify_direct_high_preventive():
    """Test direct classification with high preventive score."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.20,  # >= trigger + 0.02 (0.18)
        effective_delta=0.0,
        tactical_weight=0.5,
        soft_weight=0.5,
        config=cfg
    )
    assert label == "prophylactic_direct"
    assert score >= 0.75  # minimum direct score
    assert score <= 0.6   # capped at safety_cap
    print("✓ test_classify_direct_high_preventive PASSED")


def test_classify_latent():
    """Test latent classification."""
    cfg = ProphylaxisConfig(preventive_trigger=0.16)
    label, score = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=0.17,  # just above trigger, but no direct_gate
        effective_delta=-0.1,   # negative (worsening position)
        tactical_weight=0.7,
        soft_weight=0.4,
        config=cfg
    )
    assert label == "prophylactic_latent"
    assert score >= 0.45  # at least latent base
    print("✓ test_classify_latent PASSED")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Running prophylaxis tests...")
    print("=" * 60)

    tests = [
        test_prophylaxis_config_defaults,
        test_prophylaxis_config_immutable,
        test_prophylaxis_config_custom_values,
        test_clamp_negative_scores,
        test_clamp_zero,
        test_clamp_within_cap,
        test_clamp_above_cap,
        test_clamp_at_cap,
        test_classify_no_prophylaxis,
        test_classify_failure_case,
        test_classify_direct_high_preventive,
        test_classify_latent,
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

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
