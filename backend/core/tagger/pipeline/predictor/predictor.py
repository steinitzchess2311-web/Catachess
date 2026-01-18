from pathlib import Path
from typing import Any, Dict, List

from core.chess_engine import get_engine
from core.chess_engine.schemas import EngineLine
from core.tagger.facade import tag_position
from core.tagger.tagging import get_primary_tags

from .profile_loader import load_profile_csv
from .scoring import normalize_probabilities, score_tags

PROFILES_DIR = Path(__file__).resolve().parents[1] / "player_samples"


def predict_moves(
    fen: str,
    profile_name: str,
    *,
    depth: int = 12,
    multipv: int = 8,
    top_n: int = 3,
) -> Dict[str, Any]:
    profile_path = PROFILES_DIR / f"{profile_name}.csv"
    profile = load_profile_csv(profile_path, name=profile_name)

    engine = get_engine()
    result = engine.analyze(fen=fen, depth=depth, multipv=multipv)
    lines = [line for line in result.lines if line.pv]

    candidates: List[Dict[str, Any]] = []
    for line in lines:
        move_uci = line.pv[0]
        tag_result = tag_position(
            fen=fen,
            played_move_uci=move_uci,
            depth=depth,
            multipv=multipv,
            engine_mode="http",
        )
        tags = get_primary_tags(tag_result)
        scores = score_tags(tags, profile)
        candidates.append(_build_candidate(line, tags, scores))

    similarities = [c["similarity"] for c in candidates]
    probabilities = normalize_probabilities(similarities)
    for candidate, probability in zip(candidates, probabilities):
        candidate["probability"] = probability

    ranked = sorted(candidates, key=lambda c: c["similarity"], reverse=True)
    return {
        "profile_name": profile.name,
        "moves": ranked[:top_n],
    }


def _build_candidate(line: EngineLine, tags: List[str], scores: Dict[str, float]) -> Dict[str, Any]:
    return {
        "move": line.pv[0],
        "engine_eval": line.score,
        "similarity": scores["similarity"],
        "probability": 0.0,
        "matched_weight": scores["matched_weight"],
        "coverage": scores["coverage"],
        "tags": tags,
        "multipv": line.multipv,
    }
