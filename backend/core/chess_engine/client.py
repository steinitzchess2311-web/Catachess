# core/chess_engine/client.py
import requests
from core.config import settings
from core.chess_engine.schemas import EngineResult, EngineLine
from core.chess_engine.fallback import analyze_legal_moves
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineClient:
    """
    Client for chess engine analysis.
    Stage 11: Switched to Lichess Cloud Eval API.
    """
    
    def __init__(self, timeout: int | None = None):
        self.base_url = settings.LICHESS_CLOUD_EVAL_URL
        self.timeout = timeout or settings.ENGINE_TIMEOUT
        logger.info(f"EngineClient initialized with Lichess Cloud Eval: {self.base_url}")

    def analyze(
        self,
        fen: str,
        depth: int = 15,
        multipv: int = 3,
    ) -> EngineResult:
        logger.info(f"Analyzing (Cloud Eval): fen={fen[:50]}..., multipv={multipv}")
        
        try:
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
            
            if resp.status_code == 429:
                # Rate limit
                logger.warning("Lichess Cloud Eval rate limit (429)")
                if settings.ENGINE_FALLBACK_MODE != "off":
                    return analyze_legal_moves(fen, depth, multipv)
                raise ChessEngineError("Rate limit exceeded")
                
            if resp.status_code == 404:
                # Not found (no cloud eval available for this position)
                logger.info("Cloud eval not found (404)")
                if settings.ENGINE_FALLBACK_MODE != "off":
                    return analyze_legal_moves(fen, depth, multipv)
                raise ChessEngineError("Analysis not found in cloud")
                
            resp.raise_for_status()
            
            data = resp.json()
            return self._parse_cloud_eval(data)
            
        except requests.exceptions.Timeout:
            logger.error(f"Cloud Eval timeout after {self.timeout}s")
            if settings.ENGINE_FALLBACK_MODE != "off":
                return analyze_legal_moves(fen, depth, multipv)
            raise ChessEngineTimeoutError(self.timeout)
            
        except Exception as e:
            logger.error(f"Cloud Eval failed: {e}")
            if settings.ENGINE_FALLBACK_MODE != "off":
                return analyze_legal_moves(fen, depth, multipv)
            raise ChessEngineError(f"Engine call failed: {str(e)}")

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
            
        return EngineResult(lines=lines)