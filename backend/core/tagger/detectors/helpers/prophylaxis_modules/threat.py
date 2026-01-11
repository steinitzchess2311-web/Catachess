"""
Opponent threat estimation via engine analysis.

Matches rule_tagger2/legacy/prophylaxis.py:33-84 exactly.
"""
import chess
import chess.engine

from .config import ProphylaxisConfig


def estimate_opponent_threat(
    engine_path: str,
    board: chess.Board,
    actor: chess.Color,
    *,
    config: ProphylaxisConfig,
) -> float:
    """
    Probe the position with a fixed-depth search to estimate the opponent's
    immediate tactical resources. Used to grade prophylaxis attempts.

    Args:
        engine_path: Path to UCI chess engine
        board: Current board position
        actor: Color from whose perspective to evaluate threat
        config: Prophylaxis configuration

    Returns:
        Opponent threat score (0.0 to config.safety_cap)
    """
    temp = board.copy(stack=False)
    if temp.is_game_over():
        return 0.0

    needs_null = temp.turn == actor
    null_pushed = False

    try:
        with chess.engine.SimpleEngine.popen_uci(engine_path) as eng:
            if needs_null and not temp.is_check():
                try:
                    temp.push(chess.Move.null())
                    null_pushed = True
                except ValueError:
                    null_pushed = False

            depth = max(config.threat_depth, 8)
            info = eng.analyse(temp, chess.engine.Limit(depth=depth))
    except Exception:
        if null_pushed:
            temp.pop()
        return 0.0
    finally:
        if null_pushed and len(temp.move_stack) and temp.move_stack[-1] == chess.Move.null():
            temp.pop()

    score_obj = info.get("score")
    if score_obj is None:
        return 0.0

    try:
        pov_score = score_obj.pov(actor)
    except Exception:
        return 0.0

    if pov_score.is_mate():
        mate_in = pov_score.mate()
        if mate_in is None or mate_in > 0:
            return 0.0
        threat = 10.0 / (abs(mate_in) + 1)
    else:
        cp_value = pov_score.score(mate_score=10000) or 0
        threat = max(0.0, -cp_value / 100.0)

    return round(min(threat, config.safety_cap), 3)
