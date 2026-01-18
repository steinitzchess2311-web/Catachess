Predictor Plan (Tag-Profile Move Ranking)

Goal
- Rank the top 8 engine moves by how well their tags match a player profile.
- Output a frontend-ready payload with similarity scores and probabilities.

Inputs
- FEN string (pre-move position).
- Player profile CSV (tag,count,ratio) from `backend/core/tagger/pipeline/player_samples/`.
- Engine config (local/HTTP, depth, multipv=8 for candidate generation).

Core Data Flow
1) Load player profile(s) from CSV into normalized weights (tag -> ratio).
2) Use engine MultiPV=8 to get candidate moves (move, score_cp, kind).
3) For each candidate move:
   - Run tagger on that move (same FEN, candidate move as played_move_uci).
   - Extract fired tags (boolean fields in TagResult).
4) Score similarity vs each profile:
   - weighted_recall = sum(weights[tag] for tag in move_tags) / total_profile_weight
   - coverage = matched_tag_count / max(1, len(move_tags))
   - similarity = 0.7 * weighted_recall + 0.3 * coverage
5) Normalize similarity into per-profile probabilities across candidates.
6) Return ranked moves per profile, plus raw tags and engine meta for UI.

Frontend Hook (Stable Payload)
- schema_version: 1
- fen: string
- profiles: [
  {
    "profile_name": "DingLiren",
    "moves": [
      {
        "move_uci": "e2e4",
        "similarity": 0.42,
        "probability": 0.18,
        "matched_weight": 0.31,
        "coverage": 0.4,
        "tag_count": 5,
        "tags": ["control_over_dynamics", "neutral_maneuver"],
        "score_cp": 18,
        "kind": "quiet",
        "multipv": 1
      }
    ]
  }
]

Notes
- Keep each code file under 100 lines.
- Implement small modules: models, loader, scorer, predictor.
- Export predictor via `backend/core/tagger/pipeline/__init__.py`.
