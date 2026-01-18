from typing import Dict, List

from .models import PlayerProfile


def score_tags(tags: List[str], profile: PlayerProfile) -> Dict[str, float]:
    if not tags or profile.total_weight <= 0:
        return {
            "matched_weight": 0.0,
            "weighted_recall": 0.0,
            "coverage": 0.0,
            "similarity": 0.0,
        }

    matched_weight = sum(profile.weight_for(tag) for tag in tags)
    weighted_recall = matched_weight / profile.total_weight
    coverage = sum(1 for tag in tags if profile.weight_for(tag) > 0.0) / max(1, len(tags))
    similarity = 0.7 * weighted_recall + 0.3 * coverage

    return {
        "matched_weight": matched_weight,
        "weighted_recall": weighted_recall,
        "coverage": coverage,
        "similarity": similarity,
    }


def normalize_probabilities(scores: List[float]) -> List[float]:
    total = sum(scores)
    if total <= 0:
        return [1.0 / max(1, len(scores))] * len(scores)
    return [score / total for score in scores]
