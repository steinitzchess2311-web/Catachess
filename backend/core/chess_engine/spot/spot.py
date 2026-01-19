"""Individual spot client (based on existing EngineClient)."""
import time
import requests
from core.chess_engine.schemas import EngineResult, EngineLine
from core.chess_engine.exceptions import EngineError
from core.chess_engine.spot.models import SpotConfig, SpotMetrics, SpotStatus
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineSpot:
    """Client for a single engine spot."""

    def __init__(self, config: SpotConfig, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self.metrics = SpotMetrics(status=SpotStatus.UNKNOWN)
        logger.info(
            f"EngineSpot initialized: id={config.id}, url={config.url}, timeout={timeout}s"
        )

    def analyze(self, fen: str, depth: int = 15, multipv: int = 3) -> EngineResult:
        """
        Analyze position (copied from EngineClient.analyze).
        Records metrics on success/failure.
        """
        start_time = time.time()
        logger.info(
            f"[{self.config.id}] Analyzing: fen={fen[:50]}..., depth={depth}, multipv={multipv}"
        )

        try:
            if "/engine" in self.config.url:
                multipv_data = self._post_analyze(
                    fen=fen,
                    depth=depth,
                    multipv=multipv,
                )
            else:
                resp = requests.get(
                    f"{self.config.url}/analyze/stream",
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
                multipv_data = {}  # {multipv_num: {score, pv}}

                for line in resp.iter_lines():
                    if not line:
                        continue

                    decoded_line = line.decode('utf-8') if isinstance(line, bytes) else line

                    # SSE format: lines start with "data: "
                    if decoded_line.startswith('data: '):
                        content = decoded_line[6:]  # Remove "data: " prefix

                        # Parse UCI info lines
                        if content.startswith('info '):
                            parsed = self._parse_uci_info(content)
                            if parsed:
                                multipv_data[parsed["multipv"]] = parsed

            # Build result from collected multipv data
            if multipv_data:
                lines = [
                    EngineLine(**data)
                    for data in sorted(multipv_data.values(), key=lambda x: x['multipv'])
                ]
                result = EngineResult(lines=lines)

                # On success: update metrics
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.update_success(latency_ms)
                logger.info(
                    f"[{self.config.id}] Analysis succeeded ({latency_ms:.1f}ms, {len(lines)} lines)"
                )
                return result
            else:
                logger.error(f"[{self.config.id}] No analysis data received from stream")
                self.metrics.update_failure()
                raise ChessEngineError("No analysis data received from stream")

        except requests.exceptions.Timeout:
            self.metrics.update_failure()
            logger.error(f"[{self.config.id}] Timeout after {self.timeout}s")
            raise ChessEngineTimeoutError(self.timeout)
        except ChessEngineError:
            # Already logged and counted
            raise
        except Exception as e:
            self.metrics.update_failure()
            logger.error(f"[{self.config.id}] Request failed: {e}")
            raise ChessEngineError(f"Spot {self.config.id} failed: {str(e)}")

    def health_check(self) -> bool:
        """Quick health check (GET /health)."""
        try:
            resp = requests.get(f"{self.config.url}/health", timeout=5)
            is_healthy = resp.status_code == 200
            if is_healthy:
                logger.debug(f"[{self.config.id}] Health check: OK")
            else:
                logger.warning(f"[{self.config.id}] Health check: FAILED (status {resp.status_code})")
            return is_healthy
        except Exception as e:
            logger.warning(f"[{self.config.id}] Health check: FAILED ({e})")
            return False

    def _post_analyze(self, fen: str, depth: int, multipv: int) -> dict[int, dict]:
        resp = requests.post(
            f"{self.config.url}/analyze",
            json={
                "fen": fen,
                "depth": depth,
                "multipv": multipv,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
        info_lines = payload.get("info", [])
        multipv_data: dict[int, dict] = {}
        for line in info_lines:
            if not isinstance(line, str):
                continue
            if line.startswith("info "):
                parsed = self._parse_uci_info(line)
                if parsed:
                    multipv_data[parsed["multipv"]] = parsed
        return multipv_data

    def _parse_uci_info(self, content: str) -> dict | None:
        parts = content.split()
        if 'multipv' not in parts or 'score' not in parts or 'pv' not in parts:
            return None

        try:
            multipv_idx = parts.index('multipv')
            score_idx = parts.index('score')
            pv_idx = parts.index('pv')

            multipv_num = int(parts[multipv_idx + 1])
            score_type = parts[score_idx + 1]  # 'cp' or 'mate'
            score_value = parts[score_idx + 2]
            pv_moves = parts[pv_idx + 1:]

            if score_type == 'mate':
                score = f"mate{score_value}"
            else:
                score = int(score_value)

            return {
                'multipv': multipv_num,
                'score': score,
                'pv': pv_moves
            }
        except (ValueError, IndexError):
            return None
