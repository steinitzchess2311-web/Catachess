# PGN v2 API

## Overview
This document defines the PGN v2 endpoints used for study rendering and FEN lookup.

## GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show
Returns the ShowDTO payload for full PGN rendering.

Response fields (high level):
- headers: PGN headers
- root_fen: starting FEN
- result: game result
- nodes: node map (node_id -> node data)
- render: token stream for UI rendering

## GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/fen/{node_id}
Returns the FEN for a specific node.

Response fields:
- fen
- node_id
- san
- uci
- move_number
- color

## Feature flag
- Backend: `PGN_V2_ENABLED`
- Frontend: `localStorage.catachess_use_show_dto` (override)
