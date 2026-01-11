# CoD v2 Migration Guide

**Date**: 2026-01-11
**Status**: Complete

---

## Overview

This document explains the difference between **Legacy CoD** and **CoD v2** systems, and why catachess only implements the modern v2 system.

---

## Two CoD Systems Explained

### Legacy CoD System (9 Pattern Detectors)

**Status in catachess**: ❌ NOT IMPLEMENTED (intentionally)

**Tag Fields** (defined but unused in TagResult):
- `cod_simplify`
- `cod_plan_kill`
- `cod_freeze_bind`
- `cod_blockade_passed`
- `cod_file_seal`
- `cod_king_safety_shell`
- `cod_space_clamp`
- `cod_regroup_consolidate`
- `cod_slowdown`

**Detection Method**: Pattern-based semantic detection
- Each detector recognizes specific strategic patterns
- Uses shared control pattern functions
- Applies CoD-specific gating after pattern match

**Why NOT in catachess**:
- Legacy system from rule_tagger2
- Replaced by CoD v2's modern metrics-based approach
- More complex (9 patterns vs 4 subtypes)
- Harder to maintain and test

### CoD v2 System (4 Metric-Based Subtypes)

**Status in catachess**: ✅ FULLY IMPLEMENTED

**Location**: `detectors/cod_v2/`

**Main Tag**: `control_over_dynamics` (boolean)

**Subtype Field**: `control_over_dynamics_subtype` (string)

**Subtype Values**:
1. `"prophylaxis"` - Preventing opponent plans
2. `"piece_control"` - Restricting mobility via pieces
3. `"pawn_control"` - Restricting mobility via pawns
4. `"simplification"` - Reducing complexity via exchanges

**Subtype Boolean Tags** (added in v1.0.0):
- `cod_prophylaxis`
- `piece_control_over_dynamics`
- `pawn_control_over_dynamics`
- `control_simplification`

**Detection Method**: Metrics-based threshold detection
- Volatility drop, mobility changes, tension delta
- Gate checks (tactical_weight, mate_threat, blunder)
- 4-ply cooldown between detections
- Priority ordering (prophylaxis > piece > pawn > simplification)

**Advantages**:
- Simpler architecture (4 subtypes vs 9 patterns)
- More robust threshold-based detection
- Better diagnostics and evidence trails
- Easier to maintain and test
- Same conceptual coverage as legacy system

---

## Tag Comparison

### Legacy CoD Tags (rule_tagger2 only)

```python
# Pattern-based detectors (9 tags)
cod_simplify
cod_plan_kill
cod_freeze_bind
cod_blockade_passed
cod_file_seal
cod_king_safety_shell
cod_space_clamp
cod_regroup_consolidate
cod_slowdown
```

### CoD v2 Tags (catachess)

```python
# Main tag
control_over_dynamics: bool  # True if any subtype detected

# Subtype identifier
control_over_dynamics_subtype: str  # "prophylaxis" | "piece_control" | "pawn_control" | "simplification"

# Subtype boolean tags (for backward compatibility)
cod_prophylaxis: bool
piece_control_over_dynamics: bool
pawn_control_over_dynamics: bool
control_simplification: bool
```

---

## Using CoD v2 in catachess

### Basic Detection

```python
from core.tagger.facade import tag_position

result = tag_position(
    engine_path="/path/to/stockfish",
    fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    played_move_uci="e2e4",
)

# Check if CoD was detected
if result.control_over_dynamics:
    print(f"CoD detected: {result.control_over_dynamics_subtype}")

    # Check specific subtype boolean tags
    if result.cod_prophylaxis:
        print("Prophylactic move detected")
    elif result.piece_control_over_dynamics:
        print("Piece control detected")
    elif result.pawn_control_over_dynamics:
        print("Pawn control detected")
    elif result.control_simplification:
        print("Simplification detected")
```

### Accessing Diagnostics

```python
# Get detailed CoD v2 diagnostics
cod_diagnostics = result.analysis_context["engine_meta"]["cod_v2"]

# Diagnostics include:
# - detected: bool
# - subtype: str
# - tags: list of strings
# - gates_passed: dict
# - evidence: dict with threshold checks
```

### Subtype Descriptions

**Prophylaxis**:
- Prevents opponent's tactical or strategic plans
- Detected by volatility drop, mobility restriction, low tension
- Example: Moving a piece to block opponent's attack corridor

**Piece Control**:
- Uses pieces to restrict opponent's mobility
- Detected by opponent mobility drop + piece activity
- Example: Knight outpost that controls key squares

**Pawn Control**:
- Uses pawn structure to restrict opponent
- Detected by pawn structure changes + space control
- Example: Pawn chain that limits opponent's piece placement

**Simplification**:
- Reduces position complexity through exchanges
- Detected by piece count reduction + complexity drop
- Example: Trading pieces when ahead to reach winning endgame

---

## Migration from rule_tagger2

If you're migrating code that used legacy CoD tags:

### Legacy Tag Mapping (Approximate)

```python
# Legacy → CoD v2 approximate mapping
"cod_simplify" → "simplification"
"cod_plan_kill" → "prophylaxis"
"cod_freeze_bind" → "piece_control"
"cod_blockade_passed" → "pawn_control"
"cod_file_seal" → "pawn_control"
"cod_king_safety_shell" → "pawn_control"
"cod_space_clamp" → "pawn_control"
"cod_regroup_consolidate" → "piece_control"
"cod_slowdown" → "piece_control"
```

**Note**: This mapping is approximate. CoD v2 uses different detection criteria, so results may not match exactly.

### Code Migration Example

**Before (rule_tagger2)**:
```python
if result.cod_simplify:
    handle_simplification()
if result.cod_plan_kill:
    handle_plan_prevention()
```

**After (catachess)**:
```python
if result.control_simplification:
    handle_simplification()
if result.cod_prophylaxis:
    handle_plan_prevention()
```

---

## FAQ

**Q: Why don't the legacy cod_* fields work in catachess?**

A: They are defined in TagResult for schema compatibility but are never set to True. catachess only implements CoD v2, which uses the modern 4-subtype system.

**Q: Will legacy cod_* tags be removed?**

A: They are kept for potential future compatibility needs, but may be removed in a future major version. Use CoD v2 subtype tags instead.

**Q: How do I know which system detected a tag?**

A: In catachess, only CoD v2 is active. Check `control_over_dynamics_subtype` or the boolean subtype tags.

**Q: Are CoD v2 results compatible with rule_tagger2?**

A: Partially. Both systems detect similar concepts but use different criteria. Use the approximate mapping above for migration, but expect some differences in detection.

**Q: Can I enable legacy CoD detectors in catachess?**

A: No, they are not implemented. CoD v2 is the only available system and is considered superior.

---

## Technical Details

### Detection Thresholds

See `detectors/cod_v2/thresholds.py` for exact threshold values:

```python
# Prophylaxis thresholds
volatility_drop_cp = 15
opp_mobility_drop = 5.0
tension_delta = -3.0

# Piece control thresholds
opp_mobility_drop = 8.0
self_mobility_threshold = 10.0

# Pawn control thresholds
structure_gain = 5.0
space_gain = 5.0

# Simplification thresholds
complexity_drop = 10.0
eval_threshold = -30
```

### Gate Checks

All subtypes must pass these gates:
1. **Tactical weight** < 100 (no immediate tactics)
2. **Mate threat** = False (no mate threats)
3. **Blunder check** (eval drop < 50cp)

### Cooldown System

- 4-ply cooldown between CoD detections
- Prevents over-tagging similar moves
- Currently not enforced (requires game context tracking)

---

## Conclusion

catachess implements only **CoD v2**, the modern 4-subtype system that replaces rule_tagger2's legacy 9-pattern system. This provides:

✅ Simpler architecture
✅ Better diagnostics
✅ Easier maintenance
✅ Same conceptual coverage

Legacy cod_* tags exist in TagResult for schema compatibility but are not used. Always use CoD v2 subtype tags instead.

---

## References

- Implementation: `detectors/cod_v2/`
- Integration: `facade.py` lines 330-374
- Tests: `detectors/cod_v2/test_detector.py`
- Thresholds: `detectors/cod_v2/thresholds.py`
- Original spec: `ChessorTag_final/rule_tagger2/cod_v2/`
