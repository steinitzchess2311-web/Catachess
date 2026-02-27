# Opening Trainer Backend API (v1)

Base path: `/api/v1/opening-trainer`

## 1) Eligibility

`GET /studies/{study_id}/eligibility`

Checks whether a study can enter Opening Trainer.

Rules:
- At least one chapter starts from standard initial position.
- At least one standard-start line reaches `ply >= 5`.

## 2) Unit Catalog

`GET /studies/{study_id}/units?mode=chapter|merged&color=white|black`

Returns split tree + leaf units:
- `mode=chapter`: split inside each chapter independently.
- `mode=merged`: merge all trainable chapter lines by normalized FEN key first.
- Split trigger: opponent has >=2 replies and `ply <= 8`.
- Beyond `ply > 8`: no new split; lines remain in parent unit.

## 3) Runtime Start

`POST /studies/{study_id}/train/start`

Starts one stateless training run:
- Select unit (`unit_id` optional; defaults to first leaf unit).
- Select one line in that unit (random by optional `seed`).
- Auto-play opponent moves.
- Auto-skip mastered user steps.
- Return session state + first prompt.

Request:
```json
{
  "mode": "chapter",
  "color": "white",
  "training_mode": "quiz",
  "unit_id": "optional",
  "seed": 12345
}
```

## 4) Runtime Answer

`POST /studies/{study_id}/train/answer`

Checks one user move against current prompt and advances state.

Behavior:
- `quiz`: writes progress (`correct/wrong`, `consecutive_correct`, `mastered`).
- `learn` / `preview`: no progress write.
- SAN comparison normalizes `0-0`/`0-0-0` and strips trailing `+ # ! ?`.

Request:
```json
{
  "session": {
    "study_id": "s1",
    "mode": "chapter",
    "color": "white",
    "training_mode": "quiz",
    "unit_id": "unit_xxx",
    "line_signature": "sig",
    "line_index": 0,
    "line_count": 2,
    "step_index": 3,
    "seed": 12345
  },
  "user_move_san": "Nf3"
}
```

## 5) Progress Query

`GET /progress?fens[]=...&color=white`

Batch read step progress by normalized `from_fen` and color.

## 6) Progress Upsert

`POST /progress`

Write one attempt result for `(user_id, from_fen, move_san, color)`.

Request:
```json
{
  "from_fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq -",
  "move_san": "e4",
  "color": "white",
  "correct": true
}
```

