# core/chess_engine/client.py
import requests
from core.config import settings
from core.chess_engine.schemas import EngineResult
from core.chess_engine.exceptions import EngineError
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = (base_url or settings.ENGINE_URL).rstrip("/")
        self.timeout = timeout or settings.ENGINE_TIMEOUT
        logger.info(f"EngineClient initialized with base_url={self.base_url}, timeout={self.timeout}s")

    def analyze(
        self,
        fen: str,
        depth: int = 15,
        multipv: int = 3,
    ) -> EngineResult:
        logger.info(f"Analyzing position: fen={fen[:50]}..., depth={depth}, multipv={multipv}")
        try:
            resp = requests.get(
                f"{self.base_url}/analyze/stream",
                params={
                    "fen": fen,
                    "depth": depth,
                    "multipv": multipv,
                },
                timeout=self.timeout,
                stream=True,
            )
            resp.raise_for_status()

            # Collect streaming response (SSE format)
            from core.chess_engine.schemas import EngineLine

            # Parse UCI info lines to extract multipv data
            multipv_data = {}  # {multipv_num: {score, pv, depth}}

            for line in resp.iter_lines():
                if not line:
                    continue

                decoded_line = line.decode('utf-8') if isinstance(line, bytes) else line

                # SSE format: lines start with "data: "
                if decoded_line.startswith('data: '):
                    content = decoded_line[6:]  # Remove "data: " prefix

                    # Parse UCI info lines
                    if content.startswith('info '):
                        parts = content.split()
                        if 'multipv' in parts and 'score' in parts and 'pv' in parts:
                            try:
                                multipv_idx = parts.index('multipv')
                                score_idx = parts.index('score')
                                pv_idx = parts.index('pv')

                                multipv_num = int(parts[multipv_idx + 1])
                                score_type = parts[score_idx + 1]  # 'cp' or 'mate'
                                score_value = parts[score_idx + 2]
                                pv_moves = parts[pv_idx + 1:]

                                # Format score
                                if score_type == 'mate':
                                    score = f"mate{score_value}"
                                else:
                                    score = int(score_value)

                                # Store the multipv line data
                                multipv_data[multipv_num] = {
                                    'multipv': multipv_num,
                                    'score': score,
                                    'pv': pv_moves
                                }
                            except (ValueError, IndexError):
                                continue

            # Build result from collected multipv data
            if multipv_data:
                lines = [EngineLine(**data) for data in sorted(multipv_data.values(), key=lambda x: x['multipv'])]
                result = EngineResult(lines=lines)
                logger.info(f"Analysis complete: {len(lines)} lines received")
                return result
            else:
                logger.error("No analysis data received from stream")
                raise ChessEngineError("No analysis data received from stream")
        except requests.exceptions.Timeout:
            logger.error(f"Engine timeout after {self.timeout}s")
            raise ChessEngineTimeoutError(self.timeout)
        except ChessEngineError:
            raise
        except Exception as e:
            logger.error(f"Engine call failed: {e}")
            raise ChessEngineError(f"Engine call failed: {str(e)}")

