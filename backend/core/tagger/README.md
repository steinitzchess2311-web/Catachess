# Tagger - Chess Move Semantic Tagging System

**Version**: 2.0.0  
**Location**: `backend/core/tagger/`  
**Migration Date**: 2026-01-10

---

## Overview

The Tagger system analyzes chess positions and tags moves with semantic labels based on:
- **Tactical considerations** (sacrifices, combinations, missed tactics)
- **Positional factors** (structure, initiative, tension)
- **Strategic elements** (prophylaxis, maneuvers, space)

## Architecture

### Directory Structure

```
backend/core/tagger/
├── __init__.py              # Public API exports
├── facade.py                # Main entry point (tag_position)
├── models.py                # Data models (TagContext, TagEvidence, TagResult)
├── tag_result.py            # Tag field definitions
│
├── config/                  # Configuration
│   ├── engine.py           # Engine settings
│   └── priorities.py       # Tag priorities
│
├── engine/                  # Engine integration
│   ├── protocol.py         # Engine protocol abstraction
│   └── stockfish_client.py # Stockfish implementation
│
└── detectors/              # Tag detectors (organized by category)
    ├── helpers/            # Shared helper functions (9 modules)
    │   ├── sacrifice.py   # Sacrifice detection
    │   ├── metrics.py     # 5D position metrics
    │   ├── phase.py       # Game phase estimation
    │   ├── contact.py     # Contact ratio
    │   ├── tactical_weight.py
    │   ├── prophylaxis.py
    │   ├── maneuver.py
    │   ├── tension.py
    │   └── control.py
    │
    ├── meta/               # Meta tags (7 detectors)
    │   ├── first_choice.py
    │   ├── missed_tactic.py
    │   ├── tactical_sensitivity.py
    │   ├── conversion_precision.py
    │   ├── panic_move.py
    │   ├── tactical_recovery.py
    │   └── risk_avoidance.py
    │
    ├── opening/            # Opening tags (2 detectors)
    │   ├── central_pawn.py
    │   └── rook_pawn.py
    │
    ├── exchange/           # Exchange tags (3→1 consolidated)
    │   └── knight_bishop.py
    │
    ├── structure/          # Structure tags (3→1)
    │   └── structure.py
    │
    ├── initiative/         # Initiative tags (3→1)
    │   └── initiative.py
    │
    ├── tension/            # Tension tags (4→1)
    │   └── tension.py
    │
    ├── maneuver/           # Maneuver tags (5→1)
    │   └── maneuver.py
    │
    ├── prophylaxis/        # Prophylaxis tags (5→1)
    │   └── prophylaxis.py
    │
    └── sacrifice/          # Sacrifice tags (9→4)
        ├── tactical.py     # Tactical sacrifices
        ├── positional.py   # Positional sacrifices
        ├── combination.py  # Combination sacrifices
        └── desperate.py    # Speculative/desperate sacrifices
```

**File Reduction**: 42 detector files → 21 files (50% reduction)

---

## Usage

### Basic Usage

```python
from backend.core.tagger import tag_position

# Analyze a position
result = tag_position(
    engine_path="/usr/games/stockfish",
    fen="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    played_move_uci="e7e5",
    depth=14,
    multipv=6
)

# Check tags
print(f"First choice: {result.first_choice}")
print(f"Tactical sacrifice: {result.tactical_sacrifice}")
print(f"Positional sacrifice: {result.positional_sacrifice}")
print(f"Delta eval: {result.delta_eval:+.2f}")
print(f"Tactical weight: {result.tactical_weight:.2f}")
```

### Advanced Usage

```python
from backend.core.tagger.models import TagContext
from backend.core.tagger.detectors.sacrifice.tactical import detect_tactical_sacrifice

# Direct detector usage (for testing or custom workflows)
ctx = TagContext(
    board=board,
    played_move=move,
    best_move=best,
    # ... other fields
)

evidence = detect_tactical_sacrifice(ctx)
print(f"Fired: {evidence.fired}")
print(f"Confidence: {evidence.confidence:.2f}")
print(f"Gates passed: {evidence.gates_passed}")
print(f"Evidence: {evidence.evidence}")
```

---

## Implemented Tags (41 total)

### Meta Tags (7)
- `first_choice` - Engine's top choice
- `missed_tactic` - Missed tactical opportunity
- `tactical_sensitivity` - Accurate move in tactical position
- `conversion_precision` - Precise conversion in winning position
- `panic_move` - Panic under pressure
- `tactical_recovery` - Recovery after error
- `risk_avoidance` - Avoiding risk

### Opening Tags (2)
- `opening_central_pawn_move` - d4/e4/d5/e5 in opening
- `opening_rook_pawn_move` - a/h pawn move in opening

### Exchange Tags (3)
- `accurate_knight_bishop_exchange` - Loss < 10cp
- `inaccurate_knight_bishop_exchange` - Loss 10-30cp
- `bad_knight_bishop_exchange` - Loss > 30cp

### Structure Tags (3)
- `structural_integrity` - Maintaining structure
- `structural_compromise_dynamic` - Structure loss with compensation
- `structural_compromise_static` - Structure loss without compensation

### Initiative Tags (3)
- `initiative_exploitation` - Successfully seizing initiative
- `initiative_attempt` - Attempting initiative
- `deferred_initiative` - Quiet preparation

### Tension Tags (4)
- `tension_creation` - Creating pawn tension
- `neutral_tension_creation` - Neutral tension
- `premature_attack` - Premature attack
- `file_pressure_c` - C-file pressure

### Maneuver Tags (5)
- `constructive_maneuver` - Improving piece placement
- `constructive_maneuver_prepare` - Maneuver preparation
- `neutral_maneuver` - Neutral repositioning
- `misplaced_maneuver` - Poor piece placement
- `maneuver_opening` - Opening maneuver

### Prophylaxis Tags (5)
- `prophylactic_move` - Preventive move
- `prophylactic_direct` - High-quality prophylaxis
- `prophylactic_latent` - Subtle prophylaxis
- `prophylactic_meaningless` - Ineffective prophylaxis
- `failed_prophylactic` - Failed prevention

### Sacrifice Tags (9)
- `tactical_sacrifice` - Sound tactical sacrifice (king attack)
- `positional_sacrifice` - Sound positional sacrifice
- `tactical_combination_sacrifice` - Combination sacrifice
- `tactical_initiative_sacrifice` - Initiative sacrifice
- `positional_structure_sacrifice` - Structure sacrifice
- `positional_space_sacrifice` - Space sacrifice
- `inaccurate_tactical_sacrifice` - Unsound tactical sacrifice
- `speculative_sacrifice` - Speculative sacrifice
- `desperate_sacrifice` - Last-ditch sacrifice

---

## Sacrifice Definition (Verified ✅)

A move is classified as a **sacrifice** if:

1. **Material loss ≥ 0.5 pawns** (PIECE LOSS REQUIRED ✅)
2. **Opponent can capture** the sacrificed piece
3. **Not an even exchange** (eval delta > 0.15)

**Implementation**: `detectors/helpers/sacrifice.py:132`

```python
def is_sacrifice_candidate(ctx: TagContext) -> Tuple[bool, Dict[str, float]]:
    material_delta = compute_material_delta(board, move)
    
    # Gate 1: Material loss threshold
    if material_delta < SACRIFICE_MIN_LOSS:  # 0.5 pawns
        return False, evidence
    
    # Gate 2: Opponent can win material
    if not opponent_wins_material(board_after, target_square, piece_value):
        return False, evidence
    
    # Gate 3: Not an even exchange
    if abs(eval_delta) <= EXCHANGE_EVAL_TOLERANCE:
        return False, evidence
    
    return True, evidence
```

---

## Testing

Tests are organized in `tests/tagger/`:

```bash
# Run all tagger tests
pytest tests/tagger/ -v

# Run specific test categories
pytest tests/tagger/test_models.py -v
pytest tests/tagger/test_engine.py -v
pytest tests/tagger/test_helpers.py -v
pytest tests/tagger/test_facade.py -v
pytest tests/tagger/test_detectors_meta.py -v
```

---

## Migration Notes

**Migrated from**: `backend/modules/tagger_core/` (2026-01-10)

**Key improvements**:
- ✅ Moved to `backend/core/` for semantic clarity
- ✅ Reduced detector files by 50% (42 → 21)
- ✅ Organized detectors by category
- ✅ Consolidated related tags into single files
- ✅ Centralized all tests in `tests/tagger/`
- ✅ Verified sacrifice definition includes piece loss

**Breaking changes**:
- Import path changed: `backend.modules.tagger_core` → `backend.core.tagger`
- Some detector names changed (now use `detect_` prefix for consolidated files)

---

## Design Principles

1. **Modularity**: Each detector is independent and testable
2. **Clarity**: Related detectors grouped in single files
3. **Evidence-based**: All detections include confidence and evidence
4. **Gate system**: Clear conditions for tag firing
5. **Type safety**: Full type hints throughout

---

## Contributing

When adding new tags:

1. Choose appropriate category (or create new one)
2. Add detector function to corresponding file in `detectors/`
3. Follow naming convention: `detect_<tag_name>(ctx: TagContext) -> TagEvidence`
4. Include docstring with conditions and evidence
5. Add import to `facade.py`
6. Add test to `tests/tagger/test_detectors_<category>.py`

---

## References

- Original implementation: `ChessorTag_final/rule_tagger2/`
- Migration plan: `fixchessortag.md`
- Analysis: `chessortag.md`

