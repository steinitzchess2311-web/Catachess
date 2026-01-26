"""
Tagger pipeline orchestration.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import chess
import requests
from sqlalchemy.orm import Session

from core.tagger.versioning import get_current_version
from core.tagger.config.engine import DEFAULT_DEPTH, DEFAULT_MULTIPV
from models.tagger import FailedGame, PgnGame, PgnUpload, PlayerProfile, TagStat
from modules.tagger.errors import TaggerErrorCode, UploadStatus
from modules.tagger.storage import TaggerStorage
from modules.tagger.storage.postgres_repo import TaggerRepo
from modules.tagger.pipeline.pgn_parser import parse_pgn
from modules.tagger.pipeline.player_matcher import match_player_color
from modules.tagger.pipeline.dedupe import compute_game_hash
from modules.tagger.pipeline.tagger_runner import tag_move
from modules.tagger.pipeline.stats_aggregator import StatsAccumulator
from modules.tagger.logs import append_upload_log

logger = logging.getLogger(__name__)


class TaggerPipeline:
    def __init__(self, db: Session, storage: Optional[TaggerStorage] = None) -> None:
        self._db = db
        self._storage = storage or TaggerStorage()
        self._repo = TaggerRepo(db)

    def _update_checkpoint(self, upload: PgnUpload, updates: Dict[str, object]) -> None:
        state = dict(upload.checkpoint_state or {})
        state.update(updates)
        upload.checkpoint_state = state
        self._db.commit()

    def process_upload(self, upload: PgnUpload, player: PlayerProfile) -> None:
        logger.info("Tagger upload started: upload_id=%s player_id=%s", upload.id, player.id)
        upload.status = UploadStatus.PROCESSING.value
        self._db.commit()
        append_upload_log(self._db, upload, "Analysis started.")

        content = self._storage.get_pgn(player.id, upload.id)
        append_upload_log(self._db, upload, "PGN loaded from R2.", extra={"bytes": len(content)})
        games = list(parse_pgn(content))
        if not games:
            self._mark_upload_failed(upload, TaggerErrorCode.INVALID_PGN)
            append_upload_log(self._db, upload, "PGN parse failed: no games found.", level="error")
            return

        stats = StatsAccumulator()
        had_errors = False
        any_success = False
        candidates: List[Dict[str, str]] = []
        total_games = len(games)
        processed_games = 0
        self._update_checkpoint(upload, {
            "total_games": total_games,
            "processed_games": processed_games,
            "duplicate_games": 0,
            "last_game_index": None,
            "last_game_status": None,
            "last_game_move_count": None,
            "last_game_color": None,
        })
        logger.info("PGN parsed: total_games=%s upload_id=%s", total_games, upload.id)
        append_upload_log(self._db, upload, "PGN parsed.", extra={"total_games": total_games})

        for idx, game in enumerate(games, start=1):
            headers = game.headers
            white_name = headers.get("White")
            black_name = headers.get("Black")

            match = match_player_color(player, white_name, black_name)
            if match.color is None:
                had_errors = True
                candidates.append({"game_index": idx, "white": white_name or "", "black": black_name or ""})
                reason = match.reason or "no_match"
                error_code = TaggerErrorCode.HEADER_MISSING if reason == "header_missing" else TaggerErrorCode.MATCH_AMBIGUOUS
                moves_uci = [m.uci() for m in game.moves]
                game_hash = compute_game_hash(headers, moves_uci) if moves_uci else None
                self._record_failed_game(
                    upload=upload,
                    player=player,
                    game_index=idx,
                    headers=headers,
                    player_color=None,
                    move_count=0,
                    game_hash=game_hash,
                    error_code=error_code,
                    error_message=error_code.get_message(),
                )
                processed_games += 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "last_game_index": idx,
                    "last_game_status": error_code.value,
                    "last_game_move_count": 0,
                    "last_game_color": None,
                })
                logger.info(
                    "Game %s failed: %s upload_id=%s",
                    idx,
                    error_code.value,
                    upload.id,
                )
                append_upload_log(
                    self._db,
                    upload,
                    f"Game {idx} failed: {error_code.value}.",
                    level="error",
                )
                continue

            moves_uci = [m.uci() for m in game.moves]
            game_hash = compute_game_hash(headers, moves_uci)

            existing = self._repo.get_existing_game_id(player.id, game_hash)
            if existing:
                processed_games += 1
                state = upload.checkpoint_state or {}
                duplicate_games = int(state.get("duplicate_games", 0)) + 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "duplicate_games": duplicate_games,
                    "last_game_index": idx,
                    "last_game_status": "duplicate",
                    "last_game_move_count": len(moves_uci),
                    "last_game_color": match.color,
                })
                logger.info("Game %s skipped (duplicate) upload_id=%s", idx, upload.id)
                append_upload_log(self._db, upload, f"Game {idx} skipped (duplicate).")
                continue

            try:
                move_count = self._process_game_moves(game.board.copy(), game.moves, match.color, stats)
            except ValueError as exc:
                had_errors = True
                self._record_failed_game(
                    upload=upload,
                    player=player,
                    game_index=idx,
                    headers=headers,
                    player_color=match.color,
                    move_count=0,
                    game_hash=game_hash,
                    error_code=TaggerErrorCode.ILLEGAL_MOVE,
                    error_message=str(exc),
                )
                processed_games += 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "last_game_index": idx,
                    "last_game_status": TaggerErrorCode.ILLEGAL_MOVE.value,
                    "last_game_move_count": 0,
                    "last_game_color": match.color,
                })
                logger.info("Game %s failed: illegal_move upload_id=%s", idx, upload.id)
                append_upload_log(
                    self._db,
                    upload,
                    f"Game {idx} failed: illegal_move.",
                    level="error",
                    extra={"error_type": type(exc).__name__, "error_message": str(exc)},
                )
                continue
            except requests.Timeout as exc:
                had_errors = True
                self._record_failed_game(
                    upload=upload,
                    player=player,
                    game_index=idx,
                    headers=headers,
                    player_color=match.color,
                    move_count=0,
                    game_hash=game_hash,
                    error_code=TaggerErrorCode.ENGINE_TIMEOUT,
                    error_message=str(exc),
                )
                processed_games += 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "last_game_index": idx,
                    "last_game_status": TaggerErrorCode.ENGINE_TIMEOUT.value,
                    "last_game_move_count": 0,
                    "last_game_color": match.color,
                })
                logger.info("Game %s failed: engine_timeout upload_id=%s", idx, upload.id)
                append_upload_log(
                    self._db,
                    upload,
                    f"Game {idx} failed: engine_timeout.",
                    level="error",
                    extra={"error_type": type(exc).__name__, "error_message": str(exc)},
                )
                continue
            except requests.RequestException as exc:
                had_errors = True
                self._record_failed_game(
                    upload=upload,
                    player=player,
                    game_index=idx,
                    headers=headers,
                    player_color=match.color,
                    move_count=0,
                    game_hash=game_hash,
                    error_code=TaggerErrorCode.ENGINE_503,
                    error_message=str(exc),
                )
                processed_games += 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "last_game_index": idx,
                    "last_game_status": TaggerErrorCode.ENGINE_503.value,
                    "last_game_move_count": 0,
                    "last_game_color": match.color,
                })
                logger.info("Game %s failed: engine_503 upload_id=%s", idx, upload.id)
                append_upload_log(
                    self._db,
                    upload,
                    f"Game {idx} failed: engine_503.",
                    level="error",
                    extra={"error_type": type(exc).__name__, "error_message": str(exc)},
                )
                continue
            except Exception as exc:
                had_errors = True
                self._record_failed_game(
                    upload=upload,
                    player=player,
                    game_index=idx,
                    headers=headers,
                    player_color=match.color,
                    move_count=0,
                    game_hash=game_hash,
                    error_code=TaggerErrorCode.UNKNOWN_ERROR,
                    error_message=str(exc),
                )
                processed_games += 1
                self._update_checkpoint(upload, {
                    "processed_games": processed_games,
                    "last_game_index": idx,
                    "last_game_status": TaggerErrorCode.UNKNOWN_ERROR.value,
                    "last_game_move_count": 0,
                    "last_game_color": match.color,
                })
                logger.info("Game %s failed: unknown_error upload_id=%s", idx, upload.id)
                append_upload_log(
                    self._db,
                    upload,
                    f"Game {idx} failed: unknown_error.",
                    level="error",
                    extra={"error_type": type(exc).__name__, "error_message": str(exc)},
                )
                continue

            pgn_game = PgnGame(
                player_id=player.id,
                upload_id=upload.id,
                game_hash=game_hash,
                white_name=white_name,
                black_name=black_name,
                player_color=match.color,
                game_result=headers.get("Result"),
                move_count=move_count,
            )
            self._repo.add_pgn_game(pgn_game)
            any_success = True
            processed_games += 1
            self._update_checkpoint(upload, {
                "processed_games": processed_games,
                "last_game_index": idx,
                "last_game_status": "processed",
                "last_game_move_count": move_count,
                "last_game_color": match.color,
            })
            logger.info(
                "Game %s processed: moves=%s color=%s upload_id=%s",
                idx,
                move_count,
                match.color,
                upload.id,
            )
            append_upload_log(
                self._db,
                upload,
                f"Game {idx} analyzed.",
                extra={"moves": move_count, "color": match.color},
            )

        if candidates:
            state = upload.checkpoint_state or {}
            existing_candidates = list(state.get("candidates", []))
            state["candidates"] = existing_candidates + candidates
            upload.checkpoint_state = state

        if any_success:
            self._flush_stats(player, stats)

        if candidates:
            upload.status = UploadStatus.NEEDS_CONFIRMATION.value
        elif not any_success and had_errors:
            upload.status = UploadStatus.FAILED.value
        elif had_errors:
            upload.status = UploadStatus.COMPLETED_WITH_ERRORS.value
        else:
            upload.status = UploadStatus.DONE.value

        upload.updated_at = datetime.utcnow()
        self._db.commit()
        logger.info("Tagger upload completed: upload_id=%s status=%s", upload.id, upload.status)
        append_upload_log(self._db, upload, "Upload completed.", extra={"status": upload.status})

    def _process_game_moves(self, board: chess.Board, moves: list[chess.Move], color: str, stats: StatsAccumulator) -> int:
        player_is_white = color == "white"
        move_count = 0

        for move in moves:
            if move not in board.legal_moves:
                raise ValueError(f"Illegal move {move.uci()} at ply {board.fullmove_number}")
            if board.turn == player_is_white:
                tags, _, _ = tag_move(board.fen(), move.uci())
                stats.add_move(color)
                stats.add_tags(color, tags)
                stats.add_move("total")
                stats.add_tags("total", tags)
                move_count += 1
            board.push(move)

        return move_count

    def _record_failed_game(
        self,
        upload: PgnUpload,
        player: PlayerProfile,
        game_index: int,
        headers: Dict[str, str],
        player_color: Optional[str],
        move_count: int,
        game_hash: Optional[str],
        error_code: TaggerErrorCode,
        error_message: str,
    ) -> None:
        failed = FailedGame(
            player_id=player.id,
            upload_id=upload.id,
            game_hash=game_hash,
            game_index=game_index,
            headers=headers,
            player_color=player_color,
            move_count=move_count,
            error_code=error_code.value,
            error_message=error_message,
            retry_count=0,
            last_attempt_at=datetime.utcnow(),
        )
        self._repo.add_failed_game(failed)

    def _flush_stats(self, player: PlayerProfile, stats: StatsAccumulator) -> None:
        engine_version = get_current_version()
        stats_version = "1"

        for scope, scope_stats in stats.all_scopes().items():
            if scope_stats.total_positions == 0:
                continue

            existing_rows = self._repo.get_tag_stats(
                player_id=player.id,
                scope=scope,
                engine_version=engine_version,
                depth=DEFAULT_DEPTH,
                multipv=DEFAULT_MULTIPV,
                stats_version=stats_version,
            )
            existing_map = {row.tag_name: row for row in existing_rows}
            base_total = existing_rows[0].total_positions if existing_rows else 0
            new_total = base_total + scope_stats.total_positions

            for row in existing_rows:
                row.total_positions = new_total
                row.updated_at = datetime.utcnow()

            for tag_name, count in scope_stats.tag_counts.items():
                row = existing_map.get(tag_name)
                if row:
                    row.tag_count += count
                else:
                    self._db.add(TagStat(
                        player_id=player.id,
                        scope=scope,
                        tag_name=tag_name,
                        tag_count=count,
                        total_positions=new_total,
                        engine_version=engine_version,
                        depth=DEFAULT_DEPTH,
                        multipv=DEFAULT_MULTIPV,
                        stats_version=stats_version,
                        updated_at=datetime.utcnow(),
                    ))

    def _mark_upload_failed(self, upload: PgnUpload, error_code: TaggerErrorCode) -> None:
        upload.status = UploadStatus.FAILED.value
        upload.updated_at = datetime.utcnow()
        self._db.commit()
        append_upload_log(
            self._db,
            upload,
            "Upload failed.",
            level="error",
            extra={"error_code": error_code.value},
        )
