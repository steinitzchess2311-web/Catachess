"""
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Engine selection client for cloud eval, local workers, and legacy upstream fallback.
"""

import requests
import time
from core.config import settings
from core.chess_engine.schemas import EngineResult, EngineLine
from core.chess_engine.fallback import analyze_legal_moves
from core.chess_engine.local_workers import get_alphazero_worker, get_local_stockfish_worker
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineClient:
    """
    Client for chess engine analysis.
    Stage 11: Switched to Lichess Cloud Eval API.
    """
    
    def __init__(self, timeout: int | None = None):
        self.base_url = settings.LICHESS_CLOUD_EVAL_URL
        self.sf_url = settings.ENGINE_URL or "https://sf.catachess.com/engine/analyze"
        self.timeout = timeout or settings.ENGINE_TIMEOUT
        logger.info(f"EngineClient initialized with Lichess Cloud Eval: {self.base_url}")

    def analyze(
        self,
        fen: str,
        depth: int = 15,
        multipv: int = 3,
        engine: str | None = None,
    ) -> EngineResult:
        method_start = time.time()

        if settings.ENGINE_DISABLE_CLOUD:
            logger.info("[ENGINE CLIENT] Cloud Eval disabled; using local Stockfish")
            return get_local_stockfish_worker().analyze(fen, depth, multipv)

        if engine in ("stockfish", "local-stockfish"):
            logger.info("[ENGINE CLIENT] Engine override: local Stockfish")
            return get_local_stockfish_worker().analyze(fen, depth, multipv)

        if engine == "alphazero":
            logger.info("[ENGINE CLIENT] Engine override: AlphaZero")
            return get_alphazero_worker().analyze(fen, depth, multipv)

        if engine == "sf":
            logger.info("[ENGINE CLIENT] Engine override: local Stockfish")
            try:
                return get_local_stockfish_worker().analyze(fen, depth, multipv)
            except Exception as local_exc:
                logger.error(f"[ENGINE CLIENT] local Stockfish failed: {local_exc}")
                logger.info("[ENGINE CLIENT] Falling back to sf.catachess")
                return self._analyze_sf(fen, depth, multipv)

        logger.info(f"[ENGINE CLIENT] Attempting Cloud Eval: fen={fen[:50]}..., multipv={multipv}")

        try:
            cloud_start = time.time()
            # Lichess Cloud Eval API
            # GET https://lichess.org/api/cloud-eval?fen={fen}&multiPv={multipv}
            params = {
                "fen": fen,
                "multiPv": multipv,
                # "variant": "standard" # Default
            }
            
            resp = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            cloud_duration = time.time() - cloud_start

            if resp.status_code == 429:
                # Rate limit
                logger.warning(f"[ENGINE CLIENT] Lichess Cloud Eval rate limit (429) after {cloud_duration:.3f}s")
                logger.info("[ENGINE CLIENT] Falling back to local Stockfish due to rate limit")
                try:
                    return get_local_stockfish_worker().analyze(fen, depth, multipv)
                except Exception as sf_exc:
                    logger.error(f"[ENGINE CLIENT] local Stockfish fallback failed: {sf_exc}")
                    if settings.ENGINE_FALLBACK_MODE != "off":
                        logger.info("[ENGINE CLIENT] Final fallback to legal moves")
                        return analyze_legal_moves(fen, depth, multipv)
                    raise ChessEngineError("Rate limit exceeded")

            if resp.status_code == 404:
                # Not found (no cloud eval available for this position)
                logger.info(f"[ENGINE CLIENT] Cloud eval not found (404) after {cloud_duration:.3f}s")
                logger.info("[ENGINE CLIENT] Falling back to local Stockfish (position not in cloud)")
                try:
                    return get_local_stockfish_worker().analyze(fen, depth, multipv)
                except Exception as sf_exc:
                    logger.error(f"[ENGINE CLIENT] local Stockfish fallback failed: {sf_exc}")
                    if settings.ENGINE_FALLBACK_MODE != "off":
                        logger.info("[ENGINE CLIENT] Final fallback to legal moves")
                        return analyze_legal_moves(fen, depth, multipv)
                    raise ChessEngineError("Analysis not found in cloud")

            resp.raise_for_status()
            data = resp.json()
            result = self._parse_cloud_eval(data)
            logger.info(f"[ENGINE CLIENT] Cloud Eval success in {cloud_duration:.3f}s, {len(result.lines)} lines")
            return result
            
        except requests.exceptions.Timeout:
            cloud_duration = time.time() - cloud_start
            logger.error(f"[ENGINE CLIENT] Cloud Eval timeout after {cloud_duration:.3f}s (limit: {self.timeout}s)")
            logger.info("[ENGINE CLIENT] Falling back to local Stockfish due to timeout")
            try:
                return get_local_stockfish_worker().analyze(fen, depth, multipv)
            except Exception as sf_exc:
                logger.error(f"[ENGINE CLIENT] local Stockfish fallback failed: {sf_exc}")
                if settings.ENGINE_FALLBACK_MODE != "off":
                    logger.info("[ENGINE CLIENT] Final fallback to legal moves")
                    return analyze_legal_moves(fen, depth, multipv)
                raise ChessEngineTimeoutError(self.timeout)

        except Exception as e:
            cloud_duration = time.time() - cloud_start
            logger.error(f"[ENGINE CLIENT] Cloud Eval failed after {cloud_duration:.3f}s: {e}")
            logger.info("[ENGINE CLIENT] Falling back to local Stockfish due to error")
            try:
                return get_local_stockfish_worker().analyze(fen, depth, multipv)
            except Exception as sf_exc:
                logger.error(f"[ENGINE CLIENT] local Stockfish fallback failed: {sf_exc}")
                if settings.ENGINE_FALLBACK_MODE != "off":
                    logger.info("[ENGINE CLIENT] Final fallback to legal moves")
                    return analyze_legal_moves(fen, depth, multipv)
                raise ChessEngineError(f"Engine call failed: {str(e)}")

    def _analyze_sf(self, fen: str, depth: int, multipv: int) -> EngineResult:
        sf_total_start = time.time()
        logger.info(f"[ENGINE CLIENT - SF] Starting sf.catachess analysis: fen={fen[:50]}..., depth={depth}, multipv={multipv}")
        payload = {"fen": fen, "depth": depth, "multipv": multipv}
        headers = {
            "User-Agent": "catachess-engine/1.0",
            "Accept": "application/json",
        }
        if settings.WORKER_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.WORKER_API_TOKEN}"
        last_exc: Exception | None = None
        # Retry transient upstream errors to avoid brief CF/origin blips.
        for attempt in range(3):
            attempt_start = time.time()
            try:
                resp = requests.post(
                    self.sf_url,
                    json=payload,
                    timeout=self.timeout,
                    headers=headers,
                )
                attempt_duration = time.time() - attempt_start

                if resp.status_code in (502, 503, 504) and attempt < 2:
                    logger.warning(
                        "[ENGINE CLIENT - SF] Transient error after %.3fs: status=%s url=%s (attempt %s)",
                        attempt_duration,
                        resp.status_code,
                        resp.url,
                        attempt + 1,
                    )
                    time.sleep(0.2 * (2 ** attempt))
                    continue

                if not resp.ok:
                    body = (resp.text or "").strip()
                    if len(body) > 1000:
                        body = body[:1000] + "...(truncated)"
                    logger.error(
                        "[ENGINE CLIENT - SF] Error after %.3fs: status=%s url=%s headers=%s body=%s",
                        attempt_duration,
                        resp.status_code,
                        resp.url,
                        dict(resp.headers),
                        body,
                    )

                resp.raise_for_status()
                data = resp.json()
                result = self._parse_sf_response(data, self._fen_turn(fen))
                sf_total_duration = time.time() - sf_total_start
                logger.info(f"[ENGINE CLIENT - SF] Success in {sf_total_duration:.3f}s (attempt {attempt + 1}, this attempt: {attempt_duration:.3f}s), {len(result.lines)} lines")
                return result
            except requests.RequestException as exc:
                attempt_duration = time.time() - attempt_start
                last_exc = exc
                if attempt < 2:
                    logger.warning(
                        "[ENGINE CLIENT - SF] Request error after %.3fs: %s (attempt %s)",
                        attempt_duration,
                        exc,
                        attempt + 1,
                    )
                    time.sleep(0.2 * (2 ** attempt))
                    continue
                sf_total_duration = time.time() - sf_total_start
                logger.error(f"[ENGINE CLIENT - SF] All attempts failed after {sf_total_duration:.3f}s")
                raise ChessEngineError(f"sf.catachess request failed: {exc}") from exc

        sf_total_duration = time.time() - sf_total_start
        if last_exc is not None:
            logger.error(f"[ENGINE CLIENT - SF] All attempts failed after {sf_total_duration:.3f}s")
            raise ChessEngineError(f"sf.catachess request failed: {last_exc}") from last_exc
        logger.error(f"[ENGINE CLIENT - SF] Unknown error after {sf_total_duration:.3f}s")
        raise ChessEngineError("sf.catachess request failed: unknown error")

    def _parse_cloud_eval(self, data: dict) -> EngineResult:
        """
        Parse Lichess Cloud Eval JSON response.
        Response format example:
        {
          "fen": "...",
          "knodes": 12345,
          "depth": 50,
          "pvs": [
            {
              "moves": "e2e4 c7c5",
              "cp": 20,
              "mate": null
            }
          ]
        }
        """
        if "pvs" not in data:
            raise ChessEngineError("Invalid Cloud Eval response format")
            
        lines = []
        for i, pv in enumerate(data["pvs"]):
            # Lichess provides space-separated UCI moves string
            moves_str = pv.get("moves", "")
            uci_moves = moves_str.split()
            
            score_cp = pv.get("cp")
            score_mate = pv.get("mate")
            
            score_val = 0
            if score_mate is not None:
                score_val = f"mate{score_mate}"
            elif score_cp is not None:
                score_val = score_cp
            
            lines.append(EngineLine(
                multipv=i + 1,
                score=score_val,
                pv=uci_moves
            ))
            
        return EngineResult(lines=lines, source="CloudEval")

    def _parse_sf_response(self, data: dict, turn: str) -> EngineResult:
        if "info" not in data or not isinstance(data["info"], list):
            raise ChessEngineError("Invalid sf.catachess response format")

        entries = []
        for line in data["info"]:
            if not isinstance(line, str) or not line.startswith("info"):
                continue
            tokens = line.strip().split()
            try:
                depth_idx = tokens.index("depth")
                multipv_idx = tokens.index("multipv")
                score_idx = tokens.index("score")
                pv_idx = tokens.index("pv")
            except ValueError:
                continue

            try:
                depth = int(tokens[depth_idx + 1])
                multipv = int(tokens[multipv_idx + 1])
            except (ValueError, IndexError):
                continue

            score_type = tokens[score_idx + 1] if score_idx + 1 < len(tokens) else None
            score_val = tokens[score_idx + 2] if score_idx + 2 < len(tokens) else None
            pv_moves = tokens[pv_idx + 1 :] if pv_idx + 1 < len(tokens) else []
            if not pv_moves:
                continue

            score = 0
            if score_type == "cp" and score_val is not None:
                try:
                    score = int(score_val)
                except ValueError:
                    score = 0
            elif score_type == "mate" and score_val is not None:
                score = f"mate{score_val}"

            score = self._normalize_score_for_white(score, turn)
            entries.append((depth, multipv, score, pv_moves))

        if not entries:
            raise ChessEngineError("No usable analysis lines from sf.catachess")

        max_depth = max(d for d, _, _, _ in entries)
        per_multipv: dict[int, tuple[int, int | str, list[str]]] = {}
        for depth, multipv, score, pv_moves in entries:
            if depth != max_depth:
                continue
            per_multipv[multipv] = (depth, score, pv_moves)

        if not per_multipv:
            for depth, multipv, score, pv_moves in entries:
                prev = per_multipv.get(multipv)
                if not prev or depth > prev[0]:
                    per_multipv[multipv] = (depth, score, pv_moves)

        lines = []
        for multipv in sorted(per_multipv.keys()):
            _, score, pv_moves = per_multipv[multipv]
            lines.append(EngineLine(multipv=multipv, score=score, pv=pv_moves))

        return EngineResult(lines=lines, source="SFCata")

    @staticmethod
    def _fen_turn(fen: str) -> str:
        parts = fen.split()
        if len(parts) > 1 and parts[1] in ("w", "b"):
            return parts[1]
        return "w"

    @staticmethod
    def _normalize_score_for_white(score: int | str, turn: str) -> int | str:
        # Stockfish always returns scores from white's perspective:
        # Positive = white is better, Negative = black is better
        # No need to flip the score based on turn - keep it as-is
        return score
