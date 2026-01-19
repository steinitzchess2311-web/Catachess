"""
Main facade for the tagger system.
This is the primary entry point for tagging chess positions.
"""
from typing import Optional, Literal
import os
import chess
from .models import TagContext, Candidate
from .tag_result import TagResult
from .engine.stockfish_client import StockfishClient
from .engine.http_client import HTTPStockfishClient
from .config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV, DEFAULT_STOCKFISH_PATH

# Default HTTP engine URL (Cloudflare LB)
DEFAULT_ENGINE_URL = os.environ.get("ENGINE_URL", "https://sf.catachess.com/engine")

# Import shared modules
from .detectors.helpers.metrics import evaluation_and_metrics, metrics_delta
from .detectors.helpers.phase import estimate_phase_ratio, get_phase_bucket
from .detectors.helpers.contact import contact_ratio
from .detectors.helpers.tactical_weight import compute_tactical_weight
from .detectors.helpers.mate_threat import detect_mate_threat
from .detectors.helpers.coverage import compute_coverage_delta

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

# Import CoD v2 detector
from .detectors.cod_v2 import (
    ControlOverDynamicsV2Detector,
    CoDContext,
    CoDMetrics,
    is_cod_v2_enabled,
)

# Import versioning
from .versioning import CURRENT_VERSION, get_version_info


def tag_position(
    engine_path: Optional[str] = None,
    fen: str = "",
    played_move_uci: str = "",
    depth: int = DEFAULT_DEPTH,
    multipv: int = DEFAULT_MULTIPV,
    engine_mode: Literal["local", "http"] = "http",
    engine_url: Optional[str] = None,
) -> TagResult:
    """
    Tag a chess position and move.

    This is the main entry point matching the legacy interface.

    Args:
        engine_path: Path to Stockfish engine (for local mode)
        fen: FEN string of position before the move
        played_move_uci: UCI notation of the played move
        depth: Engine analysis depth
        multipv: Number of principal variations to analyze
        engine_mode: "local" for local Stockfish, "http" for remote service
        engine_url: Remote engine URL (for http mode, defaults to ENGINE_URL env var)

    Returns:
        TagResult with all detected tags and analysis
    """
    # Select engine client based on mode
    if engine_mode == "http":
        url = engine_url or DEFAULT_ENGINE_URL
        engine_client = HTTPStockfishClient(base_url=url)
    else:
        path = engine_path or DEFAULT_STOCKFISH_PATH
        engine_client = StockfishClient(engine_path=path)

    # Parse position and move
    board = chess.Board(fen)
    played_move = chess.Move.from_uci(played_move_uci)

    # Validate move is legal
    if played_move not in board.legal_moves:
        raise ValueError(f"Illegal move {played_move_uci} in position {fen}")

    # Run engine analysis
    with engine_client as engine:
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
    mate_threat = detect_mate_threat(board, candidates, eval_before_cp)

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

    # Compute coverage delta
    coverage_delta_value = compute_coverage_delta(board, board_played, board.turn)

    # Determine move characteristics
    is_capture = board.is_capture(played_move)
    board.push(played_move)
    is_check = board.is_check()
    board.pop()
    move_number = board.fullmove_number

    # Build tag context with all computed values
    ctx = TagContext(
        board=board,
        board_before=board,  # Same as board - it's the pre-move state
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
        coverage_delta=coverage_delta_value,
        is_capture=is_capture,
        is_check=is_check,
        move_number=move_number,
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

    # CoD v2 detection
    cod_detected = False
    cod_subtype = None
    cod_prophylaxis_tag = False
    piece_control_tag = False
    pawn_control_tag = False
    control_simplification_tag = False

    if is_cod_v2_enabled():
        # Build CoD metrics from context
        cod_metrics = CoDMetrics(
            volatility_drop_cp=abs(delta_eval * 100),
            eval_drop_cp=int(delta_eval * 100),
            opp_mobility_drop=opp_component_deltas.get("mobility", 0.0),
            self_mobility_change=component_deltas.get("mobility", 0.0),
            tension_delta=component_deltas.get("tension", 0.0),
            structure_gain=component_deltas.get("structure", 0.0),
            king_safety_gain=component_deltas.get("king_safety", 0.0),
            space_gain=component_deltas.get("space", 0.0),
            preventive_score=prophylaxis_score,
            threat_delta=0.0,  # TODO: Compute from followup analysis
        )

        # Build CoD context
        cod_ctx = CoDContext(
            board=board,
            played_move=played_move,
            actor=board.turn,
            metrics=cod_metrics,
            eval_drop_cp=int(delta_eval * 100),
            played_kind=played_kind,
            current_ply=0,  # TODO: Track ply count
            last_cod_ply=-999,  # TODO: Track from game state
            phase_bucket=phase_bucket,
            allow_positional=(phase_bucket in ("middlegame", "endgame")),
            has_dynamic_in_band=has_dynamic_in_band,
            control_cfg={
                "tactical_weight": tac_weight,
                "mate_threat": mate_threat,
            },
        )

        # Run detector
        cod_detector = ControlOverDynamicsV2Detector()
        cod_result = cod_detector.detect(cod_ctx)

        if cod_result.detected:
            cod_detected = True
            cod_subtype = cod_result.subtype.value
            engine_meta["cod_v2"] = cod_result.to_dict()

            # Map subtype to specific boolean tags
            if cod_subtype == "prophylaxis":
                cod_prophylaxis_tag = True
            elif cod_subtype == "piece_control":
                piece_control_tag = True
            elif cod_subtype == "pawn_control":
                pawn_control_tag = True
            elif cod_subtype == "simplification":
                control_simplification_tag = True

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
        # CoD v2 tags
        control_over_dynamics=cod_detected,
        control_over_dynamics_subtype=cod_subtype,
        cod_prophylaxis=cod_prophylaxis_tag,
        piece_control_over_dynamics=piece_control_tag,
        pawn_control_over_dynamics=pawn_control_tag,
        control_simplification=control_simplification_tag,
        mode=mode,
        analysis_context={
            "engine_meta": engine_meta,
            "phase_ratio": phase_ratio,
            "phase_bucket": phase_bucket,
            "tactical_weight": tac_weight,
            "contact_ratio": contact_ratio_before,
            "version": CURRENT_VERSION,
            "version_info": get_version_info(),
        },
    )

    return result


__all__ = ["tag_position"]
