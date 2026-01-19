# core/chess_engine/client.py
import requests
from core.config import settings
from core.chess_engine.schemas import EngineResult
from core.chess_engine.fallback import analyze_legal_moves
from core.chess_engine.exceptions import EngineError
from core.log.log_chess_engine import logger
from core.errors import ChessEngineError, ChessEngineTimeoutError


class EngineClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.base_url = self._normalize_base_url(base_url or settings.ENGINE_URL)
        self.timeout = timeout or settings.ENGINE_TIMEOUT
        logger.info(f"EngineClient initialized with base_url={self.base_url}, timeout={self.timeout}s")

    def analyze(
        self,
        fen: str,
        depth: int = 15,
        multipv: int = 3,
    ) -> EngineResult:
        logger.info(f"Analyzing position: fen={fen[:50]}..., depth={depth}, multipv={multipv}")
        if not self.base_url:
            self.last_spot_id = "fallback"
            return analyze_legal_moves(fen, depth, multipv)
        try:
            if "/engine" in self.base_url:
                multipv_data = self._post_analyze(
                    fen=fen,
                    depth=depth,
                    multipv=multipv,
                )
            else:
                multipv_data = self._stream_analyze(
                    fen=fen,
                    depth=depth,
                    multipv=multipv,
                )
            self.last_spot_id = "single"
            return self._build_result(multipv_data)
        except requests.exceptions.Timeout:
            logger.error(f"Engine timeout after {self.timeout}s")
            if settings.ENGINE_FALLBACK_MODE != "off":
                self.last_spot_id = "fallback"
                return analyze_legal_moves(fen, depth, multipv)
            raise ChessEngineTimeoutError(self.timeout)
        except ChessEngineError:
            raise
        except Exception as e:
            logger.error(f"Engine call failed: {e}")
            if settings.ENGINE_FALLBACK_MODE != "off":
                self.last_spot_id = "fallback"
                return analyze_legal_moves(fen, depth, multipv)
            raise ChessEngineError(f"Engine call failed: {str(e)}")

    def _post_analyze(self, fen: str, depth: int, multipv: int) -> dict[int, dict]:
        resp = requests.post(
            f"{self.base_url}/analyze",
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
        multipv_data = {}
        for line in info_lines:
            if not isinstance(line, str):
                continue
            if line.startswith("info "):
                parsed = self._parse_uci_info(line)
                if parsed:
                    multipv_data[parsed["multipv"]] = parsed
        return multipv_data

    def _stream_analyze(self, fen: str, depth: int, multipv: int) -> dict[int, dict]:
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

        multipv_data = {}
        for line in resp.iter_lines():
            if not line:
                continue
            decoded_line = line.decode('utf-8') if isinstance(line, bytes) else line
            if decoded_line.startswith('data: '):
                content = decoded_line[6:]
                if content.startswith('info '):
                    parsed = self._parse_uci_info(content)
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
            score_type = parts[score_idx + 1]
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

    def _build_result(self, multipv_data: dict[int, dict]) -> EngineResult:
        from core.chess_engine.schemas import EngineLine

        if not multipv_data:
            logger.error("No analysis data received from engine")
            raise ChessEngineError("No analysis data received from engine")

        lines = [EngineLine(**data) for data in sorted(multipv_data.values(), key=lambda x: x['multipv'])]
        result = EngineResult(lines=lines)
        logger.info(f"Analysis complete: {len(lines)} lines received")
        return result

    @staticmethod
    def _normalize_base_url(base_url: str | None) -> str:
        if not base_url:
            return ""
        url = base_url.rstrip("/")
        if url.endswith("/analyze/stream"):
            url = url[: -len("/analyze/stream")]
        if url.endswith("/analyze"):
            url = url[: -len("/analyze")]
        return url
