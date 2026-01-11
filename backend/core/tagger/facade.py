"""
Main facade for the tagger system.
This is the primary entry point for tagging chess positions.
"""
from typing import Optional
import chess
from .models import TagContext, Candidate
from .tag_result import TagResult
from .engine.stockfish_client import StockfishClient
from .config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_STOCKFISH_PATH

# Import shared modules
from .detectors.helpers.metrics import evaluation_and_metrics, metrics_delta
from .detectors.helpers.phase import estimate_phase_ratio, get_phase_bucket
from .detectors.helpers.contact import contact_ratio
from .detectors.helpers.tactical_weight import compute_tactical_weight

# Import Meta tag detectors
from .detectors.meta import first_choice, missed_tactic, tactical_sensitivity
from .detectors.meta import conversion_precision, panic_move, tactical_recovery, risk_avoidance

# Import Opening detectors
from .detectors.opening import central_pawn as opening_central_pawn_move
from .detectors.opening import rook_pawn as opening_rook_pawn_move

# Import Exchange detectors
from .detectors.exchange.knight_bishop import (
    detect_accurate_knight_bishop_exchange,
    detect_inaccurate_knight_bishop_exchange,
    detect_bad_knight_bishop_exchange,
)

# Import Structure detectors
from .detectors.structure.structure import (
    detect_structural_integrity,
    detect_structural_compromise_dynamic,
    detect_structural_compromise_static,
)

# Import Initiative detectors
from .detectors.initiative.initiative import (
    detect_initiative_exploitation,
    detect_initiative_attempt,
    detect_deferred_initiative,
)

# Import Tension detectors
from .detectors.tension.tension import (
    detect_tension_creation,
    detect_neutral_tension_creation,
    detect_premature_attack,
    detect_file_pressure_c,
)

# Import Maneuver detectors
from .detectors.maneuver.maneuver import (
    detect_constructive_maneuver,
    detect_constructive_maneuver_prepare,
    detect_neutral_maneuver,
    detect_misplaced_maneuver,
    detect_maneuver_opening,
)

# Import Prophylaxis detectors
from .detectors.prophylaxis.prophylaxis import (
    detect_prophylactic_move,
    detect_prophylactic_direct,
    detect_prophylactic_latent,
    detect_prophylactic_meaningless,
    detect_failed_prophylactic,
)

# Import Sacrifice detectors
from .detectors.sacrifice.tactical import (
    detect_tactical_sacrifice,
    detect_inaccurate_tactical_sacrifice,
)
from .detectors.sacrifice.positional import (
    detect_positional_sacrifice,
    detect_positional_structure_sacrifice,
    detect_positional_space_sacrifice,
)
from .detectors.sacrifice.combination import (
    detect_tactical_combination_sacrifice,
    detect_tactical_initiative_sacrifice,
)
from .detectors.sacrifice.desperate import (
    detect_speculative_sacrifice,
    detect_desperate_sacrifice,
)


def tag_position(
    engine_path: Optional[str],
    fen: str,
    played_move_uci: str,
    depth: int = DEFAULT_DEPTH,
    multipv: int = DEFAULT_MULTIPV,
) -> TagResult:
    """
    Tag a chess position and move.

    This is the main entry point matching the legacy interface.

    Args:
        engine_path: Path to Stockfish engine
        fen: FEN string of position before the move
        played_move_uci: UCI notation of the played move
        depth: Engine analysis depth
        multipv: Number of principal variations to analyze

    Returns:
        TagResult with all detected tags and analysis
    """
    # Use default engine path if not specified
    if engine_path is None:
        engine_path = DEFAULT_STOCKFISH_PATH

    # Parse position and move
    board = chess.Board(fen)
    played_move = chess.Move.from_uci(played_move_uci)

    # Validate move is legal
    if played_move not in board.legal_moves:
        raise ValueError(f"Illegal move {played_move_uci} in position {fen}")

    # Run engine analysis
    with StockfishClient(engine_path) as engine:
        # Analyze candidates in the position before the move
        candidates, eval_before_cp, engine_meta = engine.analyse_candidates(
            board, depth, multipv
        )

        # Get evaluation after the played move
        eval_played_cp = engine.eval_specific(board, played_move, depth)

    # Determine best move and its evaluation
    best_move = candidates[0].move if candidates else played_move
    best_kind = candidates[0].kind if candidates else "quiet"
    eval_best_cp = candidates[0].score_cp if candidates else eval_before_cp

    # Find played move in candidates to get its kind
    played_kind = "quiet"
    for cand in candidates:
        if cand.move == played_move:
            played_kind = cand.kind
            break

    # Convert to normalized float scores
    eval_before = eval_before_cp / 100.0
    eval_played = eval_played_cp / 100.0
    eval_best = eval_best_cp / 100.0
    delta_eval = eval_played - eval_before

    # Compute game phase
    phase_ratio = estimate_phase_ratio(board)
    phase_bucket = get_phase_bucket(phase_ratio)

    # Compute contact ratios
    contact_ratio_before = contact_ratio(board)

    # Create boards for played and best moves
    board_played = board.copy()
    board_played.push(played_move)
    contact_ratio_played = contact_ratio(board_played)

    board_best = board.copy()
    board_best.push(best_move)
    contact_ratio_best = contact_ratio(board_best)

    # Compute position metrics (5 dimensions) for each state
    metrics_before, opp_metrics_before, _ = evaluation_and_metrics(board, board.turn)
    metrics_played, opp_metrics_played, _ = evaluation_and_metrics(board_played, board.turn)
    metrics_best, opp_metrics_best, _ = evaluation_and_metrics(board_best, board.turn)

    # Compute metric deltas
    component_deltas = metrics_delta(metrics_before, metrics_played)
    opp_component_deltas = metrics_delta(opp_metrics_before, opp_metrics_played)

    # Compute tactical weight
    delta_tactics = component_deltas.get("tactics", 0.0)
    delta_structure = component_deltas.get("structure", 0.0)
    depth_jump_cp = engine_meta.get("depth_jump_cp", 0)
    deepening_gain_cp = engine_meta.get("deepening_gain_cp", 0)
    score_gap_cp = abs(eval_best_cp - candidates[1].score_cp) if len(candidates) > 1 else 0
    best_is_forcing = best_kind in ("dynamic", "forcing")
    played_is_forcing = played_kind in ("dynamic", "forcing")
    mate_threat = False  # TODO: Detect mate threats

    tac_weight = compute_tactical_weight(
        delta_eval_cp=int(delta_eval * 100),
        delta_tactics=delta_tactics,
        delta_structure=delta_structure,
        depth_jump_cp=depth_jump_cp,
        deepening_gain_cp=deepening_gain_cp,
        score_gap_cp=score_gap_cp,
        contact_ratio=contact_ratio_before,
        phase_ratio=phase_ratio,
        best_is_forcing=best_is_forcing,
        played_is_forcing=played_is_forcing,
        mate_threat=mate_threat,
    )

    # Check if there are dynamic moves in the candidate band
    has_dynamic_in_band = any(c.kind in ("dynamic", "forcing") for c in candidates)

    # Build tag context with all computed values
    ctx = TagContext(
        board=board,
        fen=fen,
        played_move=played_move,
        actor=board.turn,
        candidates=candidates,
        best_move=best_move,
        played_kind=played_kind,
        best_kind=best_kind,
        eval_before_cp=eval_before_cp,
        eval_played_cp=eval_played_cp,
        eval_best_cp=eval_best_cp,
        eval_before=eval_before,
        eval_played=eval_played,
        eval_best=eval_best,
        delta_eval=delta_eval,
        metrics_before=metrics_before,
        metrics_played=metrics_played,
        metrics_best=metrics_best,
        component_deltas=component_deltas,
        opp_metrics_before=opp_metrics_before,
        opp_metrics_played=opp_metrics_played,
        opp_metrics_best=opp_metrics_best,
        opp_component_deltas=opp_component_deltas,
        phase_ratio=phase_ratio,
        phase_bucket=phase_bucket,
        contact_ratio_before=contact_ratio_before,
        contact_ratio_played=contact_ratio_played,
        contact_ratio_best=contact_ratio_best,
        tactical_weight=tac_weight,
        coverage_delta=0,  # TODO: Implement coverage tracking
        has_dynamic_in_band=has_dynamic_in_band,
        analysis_meta=engine_meta,
        engine_depth=depth,
        engine_multipv=multipv,
    )

    # Run tag detectors
    # Meta tags
    first_choice_evidence = first_choice.detect(ctx)
    missed_tactic_evidence = missed_tactic.detect(ctx)
    tactical_sensitivity_evidence = tactical_sensitivity.detect(ctx)
    conversion_precision_evidence = conversion_precision.detect(ctx)
    panic_move_evidence = panic_move.detect(ctx)
    tactical_recovery_evidence = tactical_recovery.detect(ctx)
    risk_avoidance_evidence = risk_avoidance.detect(ctx)

    # Opening tags
    opening_central_evidence = opening_central_pawn_move.detect(ctx)
    opening_rook_evidence = opening_rook_pawn_move.detect(ctx)

    # Knight-Bishop exchange tags
    accurate_kb_exchange_evidence = detect_accurate_knight_bishop_exchange(ctx)
    inaccurate_kb_exchange_evidence = detect_inaccurate_knight_bishop_exchange(ctx)
    bad_kb_exchange_evidence = detect_bad_knight_bishop_exchange(ctx)

    # Structure tags
    structural_integrity_evidence = detect_structural_integrity(ctx)
    structural_compromise_dynamic_evidence = detect_structural_compromise_dynamic(ctx)
    structural_compromise_static_evidence = detect_structural_compromise_static(ctx)

    # Initiative tags
    initiative_exploitation_evidence = detect_initiative_exploitation(ctx)
    initiative_attempt_evidence = detect_initiative_attempt(ctx)
    deferred_initiative_evidence = detect_deferred_initiative(ctx)

    # Tension tags
    tension_creation_evidence = detect_tension_creation(ctx)
    neutral_tension_creation_evidence = detect_neutral_tension_creation(ctx)
    premature_attack_evidence = detect_premature_attack(ctx)
    file_pressure_c_evidence = detect_file_pressure_c(ctx)

    # Maneuver tags
    constructive_maneuver_evidence = detect_constructive_maneuver(ctx)
    constructive_maneuver_prepare_evidence = detect_constructive_maneuver_prepare(ctx)
    neutral_maneuver_evidence = detect_neutral_maneuver(ctx)
    misplaced_maneuver_evidence = detect_misplaced_maneuver(ctx)
    maneuver_opening_evidence = detect_maneuver_opening(ctx)

    # Prophylaxis tags
    prophylactic_move_evidence = detect_prophylactic_move(ctx)
    prophylactic_direct_evidence = detect_prophylactic_direct(ctx)
    prophylactic_latent_evidence = detect_prophylactic_latent(ctx)
    prophylactic_meaningless_evidence = detect_prophylactic_meaningless(ctx)
    failed_prophylactic_evidence = detect_failed_prophylactic(ctx)

    # Determine prophylaxis score
    prophylaxis_score = 0.0
    if prophylactic_direct_evidence.fired:
        prophylaxis_score = prophylactic_direct_evidence.confidence
    elif prophylactic_latent_evidence.fired:
        prophylaxis_score = prophylactic_latent_evidence.confidence
    elif prophylactic_move_evidence.fired:
        prophylaxis_score = prophylactic_move_evidence.confidence

    # Sacrifice tags
    tactical_sacrifice_evidence = detect_tactical_sacrifice(ctx)
    positional_sacrifice_evidence = detect_positional_sacrifice(ctx)
    inaccurate_tactical_sacrifice_evidence = detect_inaccurate_tactical_sacrifice(ctx)
    speculative_sacrifice_evidence = detect_speculative_sacrifice(ctx)
    desperate_sacrifice_evidence = detect_desperate_sacrifice(ctx)
    tactical_combination_sacrifice_evidence = detect_tactical_combination_sacrifice(ctx)
    tactical_initiative_sacrifice_evidence = detect_tactical_initiative_sacrifice(ctx)
    positional_structure_sacrifice_evidence = detect_positional_structure_sacrifice(ctx)
    positional_space_sacrifice_evidence = detect_positional_space_sacrifice(ctx)

    # Determine mode from evaluation
    if eval_before >= 2.0:
        mode = "winning"
    elif eval_before <= -2.0:
        mode = "losing"
    else:
        mode = "neutral"

    # Build result with all detected tags
    result = TagResult(
        played_move=played_move_uci,
        played_kind=played_kind,
        best_move=best_move.uci(),
        best_kind=best_kind,
        eval_before=eval_before,
        eval_played=eval_played,
        eval_best=eval_best,
        delta_eval=delta_eval,
        # Meta tags
        first_choice=first_choice_evidence.fired,
        missed_tactic=missed_tactic_evidence.fired,
        tactical_sensitivity=tactical_sensitivity_evidence.fired,
        conversion_precision=conversion_precision_evidence.fired,
        panic_move=panic_move_evidence.fired,
        tactical_recovery=tactical_recovery_evidence.fired,
        risk_avoidance=risk_avoidance_evidence.fired,
        # Opening tags
        opening_central_pawn_move=opening_central_evidence.fired,
        opening_rook_pawn_move=opening_rook_evidence.fired,
        # Knight-Bishop exchange tags
        accurate_knight_bishop_exchange=accurate_kb_exchange_evidence.fired,
        inaccurate_knight_bishop_exchange=inaccurate_kb_exchange_evidence.fired,
        bad_knight_bishop_exchange=bad_kb_exchange_evidence.fired,
        # Structure tags
        structural_integrity=structural_integrity_evidence.fired,
        structural_compromise_dynamic=structural_compromise_dynamic_evidence.fired,
        structural_compromise_static=structural_compromise_static_evidence.fired,
        # Initiative tags
        initiative_exploitation=initiative_exploitation_evidence.fired,
        initiative_attempt=initiative_attempt_evidence.fired,
        deferred_initiative=deferred_initiative_evidence.fired,
        # Tension tags
        tension_creation=tension_creation_evidence.fired,
        neutral_tension_creation=neutral_tension_creation_evidence.fired,
        premature_attack=premature_attack_evidence.fired,
        file_pressure_c=file_pressure_c_evidence.fired,
        # Maneuver tags
        constructive_maneuver=constructive_maneuver_evidence.fired,
        constructive_maneuver_prepare=constructive_maneuver_prepare_evidence.fired,
        neutral_maneuver=neutral_maneuver_evidence.fired,
        misplaced_maneuver=misplaced_maneuver_evidence.fired,
        maneuver_opening=maneuver_opening_evidence.fired,
        # Prophylaxis tags
        prophylactic_move=prophylactic_move_evidence.fired,
        prophylactic_direct=prophylactic_direct_evidence.fired,
        prophylactic_latent=prophylactic_latent_evidence.fired,
        prophylactic_meaningless=prophylactic_meaningless_evidence.fired,
        failed_prophylactic=failed_prophylactic_evidence.fired,
        prophylaxis_score=prophylaxis_score,
        # Sacrifice tags
        tactical_sacrifice=tactical_sacrifice_evidence.fired,
        positional_sacrifice=positional_sacrifice_evidence.fired,
        inaccurate_tactical_sacrifice=inaccurate_tactical_sacrifice_evidence.fired,
        speculative_sacrifice=speculative_sacrifice_evidence.fired,
        desperate_sacrifice=desperate_sacrifice_evidence.fired,
        tactical_combination_sacrifice=tactical_combination_sacrifice_evidence.fired,
        tactical_initiative_sacrifice=tactical_initiative_sacrifice_evidence.fired,
        positional_structure_sacrifice=positional_structure_sacrifice_evidence.fired,
        positional_space_sacrifice=positional_space_sacrifice_evidence.fired,
        mode=mode,
        analysis_context={
            "engine_meta": engine_meta,
            "phase_ratio": phase_ratio,
            "phase_bucket": phase_bucket,
            "tactical_weight": tac_weight,
            "contact_ratio": contact_ratio_before,
        },
    )

    return result


__all__ = ["tag_position"]
