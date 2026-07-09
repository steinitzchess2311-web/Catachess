"""
Created at: 2026-07-08 22:55 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:30 EDT
Last Modified by: Codex

Local server-side chess engine workers and shared cross-process slot limits.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
import fcntl
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from core.chess_engine.schemas import EngineLine, EngineResult
from core.config import settings
from core.errors import ChessEngineError, ChessEngineTimeoutError
from core.log.log_chess_engine import logger


@dataclass(frozen=True)
class EngineCapability:
    """Runtime capability reported by an engine worker."""

    key: str
    label: str
    available: bool
    status: str
    detail: str
    concurrency_limit: int
    active_workers: int
    binary: str | None = None


def _positive_int(value: int, fallback: int) -> int:
    return value if isinstance(value, int) and value > 0 else fallback


class CrossProcessSlotLimiter:
    """Small file-lock based slot limiter shared by gunicorn processes."""

    def __init__(self, name: str, limit: int, root: str | None = None) -> None:
        self.name = name
        self.limit = _positive_int(limit, 1)
        self.root = Path(root or settings.ENGINE_SLOT_LOCK_DIR)
        self.root.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def acquire(self, timeout: int) -> Iterator[None]:
        deadline = time.time() + timeout
        handles: list[Any] = []
        try:
            while time.time() < deadline:
                for slot in range(self.limit):
                    lock_path = self.root / f"{self.name}.{slot}.lock"
                    handle = open(lock_path, "a+")
                    try:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    except BlockingIOError:
                        handle.close()
                        continue
                    handles.append(handle)
                    yield
                    return
                time.sleep(0.05)
            raise ChessEngineTimeoutError(timeout)
        finally:
            for handle in handles:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                finally:
                    handle.close()


class LocalStockfishWorker:
    """Short-lived UCI Stockfish process runner protected by a slot limiter."""

    def __init__(
        self,
        binary_path: str | None = None,
        max_workers: int | None = None,
        timeout: int | None = None,
    ) -> None:
        configured_binary = binary_path or settings.STOCKFISH_BINARY_PATH
        self.binary_path = configured_binary or shutil.which("stockfish") or "/usr/games/stockfish"
        self.max_workers = _positive_int(max_workers or settings.STOCKFISH_MAX_WORKERS, 10)
        self.timeout = _positive_int(timeout or settings.ENGINE_TIMEOUT, 60)
        self._slot_limiter = CrossProcessSlotLimiter("stockfish", self.max_workers)
        self._active_workers = 0
        self._lock = threading.Lock()

    @property
    def active_workers(self) -> int:
        with self._lock:
            return self._active_workers

    def capability(self) -> EngineCapability:
        binary_exists = bool(self.binary_path and Path(self.binary_path).exists())
        return EngineCapability(
            key="stockfish",
            label="Stockfish",
            available=binary_exists,
            status="available" if binary_exists else "unavailable",
            detail=(
                f"Using {self.binary_path}"
                if binary_exists
                else f"Stockfish binary not found at {self.binary_path}"
            ),
            concurrency_limit=self.max_workers,
            active_workers=self.active_workers,
            binary=self.binary_path,
        )

    def analyze(self, fen: str, depth: int, multipv: int) -> EngineResult:
        if not Path(self.binary_path).exists():
            raise ChessEngineError(f"Stockfish binary not found: {self.binary_path}")

        start = time.time()
        with self._slot_limiter.acquire(timeout=self.timeout):
            with self._lock:
                self._active_workers += 1
            try:
                return self._run_uci(fen=fen, depth=depth, multipv=multipv)
            finally:
                with self._lock:
                    self._active_workers -= 1
                logger.info(
                    "[LOCAL STOCKFISH] request finished in %.3fs active=%s/%s",
                    time.time() - start,
                    self.active_workers,
                    self.max_workers,
                )

    def _run_uci(self, fen: str, depth: int, multipv: int) -> EngineResult:
        bounded_depth = max(1, min(int(depth), settings.STOCKFISH_MAX_DEPTH))
        bounded_multipv = max(1, min(int(multipv), settings.STOCKFISH_MAX_MULTIPV))

        proc = subprocess.Popen(
            [self.binary_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None

        info_lines: list[str] = []
        try:
            self._send(proc, "uci")
            self._read_until(proc, "uciok", timeout=5)
            self._send(proc, f"setoption name Threads value {settings.STOCKFISH_THREADS_PER_WORKER}")
            self._send(proc, f"setoption name Hash value {settings.STOCKFISH_HASH_MB}")
            self._send(proc, f"setoption name MultiPV value {bounded_multipv}")
            self._send(proc, "isready")
            self._read_until(proc, "readyok", timeout=5)
            self._send(proc, f"position fen {fen}")
            self._send(proc, f"go depth {bounded_depth}")

            deadline = time.time() + self.timeout
            while time.time() < deadline:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("info "):
                    info_lines.append(line)
                if line.startswith("bestmove"):
                    break

            if time.time() >= deadline:
                raise ChessEngineTimeoutError(self.timeout)

            lines = parse_stockfish_info_lines(info_lines, self._fen_turn(fen))
            if not lines:
                raise ChessEngineError("No usable Stockfish analysis lines")
            return EngineResult(lines=lines, source="LocalStockfish")
        finally:
            self._send_quit(proc)

    @staticmethod
    def _send(proc: subprocess.Popen[str], command: str) -> None:
        if proc.stdin is None:
            raise ChessEngineError("Stockfish stdin closed")
        proc.stdin.write(command + "\n")
        proc.stdin.flush()

    @staticmethod
    def _read_until(proc: subprocess.Popen[str], expected: str, timeout: int) -> list[str]:
        if proc.stdout is None:
            raise ChessEngineError("Stockfish stdout closed")
        deadline = time.time() + timeout
        lines: list[str] = []
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            lines.append(line)
            if expected in line:
                return lines
        raise ChessEngineTimeoutError(timeout)

    @staticmethod
    def _send_quit(proc: subprocess.Popen[str]) -> None:
        try:
            if proc.poll() is None and proc.stdin is not None:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
                proc.wait(timeout=2)
        except Exception:
            proc.kill()

    @staticmethod
    def _fen_turn(fen: str) -> str:
        parts = fen.split()
        if len(parts) > 1 and parts[1] in ("w", "b"):
            return parts[1]
        return "w"


class AlphaZeroWorker:
    """AlphaZero worker registration with strict unavailable semantics."""

    def __init__(self, max_workers: int | None = None, timeout: int | None = None) -> None:
        self.max_workers = _positive_int(max_workers or settings.ALPHAZERO_MAX_WORKERS, 1)
        self.timeout = _positive_int(timeout or settings.ALPHAZERO_TIMEOUT, 60)
        self._slot_limiter = CrossProcessSlotLimiter("alphazero", self.max_workers)
        self._active_workers = 0
        self._lock = threading.Lock()

    @property
    def active_workers(self) -> int:
        with self._lock:
            return self._active_workers

    def capability(self) -> EngineCapability:
        command = settings.ALPHAZERO_COMMAND.strip()
        model_path = settings.ALPHAZERO_MODEL_PATH.strip()
        gpu_ready = self._gpu_available()
        model_ready = bool(model_path and Path(model_path).exists())
        command_ready = bool(command)
        available = command_ready and model_ready and gpu_ready

        missing: list[str] = []
        if not command_ready:
            missing.append("ALPHAZERO_COMMAND")
        if not model_ready:
            missing.append("ALPHAZERO_MODEL_PATH")
        if not gpu_ready:
            missing.append("GPU driver")

        return EngineCapability(
            key="alphazero",
            label="AlphaZero",
            available=available,
            status="available" if available else "unavailable",
            detail="ready" if available else "Missing " + ", ".join(missing),
            concurrency_limit=self.max_workers,
            active_workers=self.active_workers,
            binary=command or None,
        )

    def analyze(self, fen: str, depth: int, multipv: int) -> EngineResult:
        capability = self.capability()
        if not capability.available:
            raise ChessEngineError(f"AlphaZero unavailable: {capability.detail}")

        with self._slot_limiter.acquire(timeout=self.timeout):
            with self._lock:
                self._active_workers += 1
            try:
                return self._run_command(fen=fen, depth=depth, multipv=multipv)
            finally:
                with self._lock:
                    self._active_workers -= 1

    def _run_command(self, fen: str, depth: int, multipv: int) -> EngineResult:
        command = settings.ALPHAZERO_COMMAND.strip()
        model_path = settings.ALPHAZERO_MODEL_PATH.strip()
        env = os.environ.copy()
        env["CATA_ENGINE_FEN"] = fen
        env["CATA_ENGINE_DEPTH"] = str(depth)
        env["CATA_ENGINE_MULTIPV"] = str(multipv)
        env["CATA_ENGINE_MODEL_PATH"] = model_path
        env["CUDA_VISIBLE_DEVICES"] = settings.ALPHAZERO_CUDA_VISIBLE_DEVICES

        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=self.timeout,
            env=env,
        )
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            raise ChessEngineError(f"AlphaZero command failed: {stderr[:500]}")
        try:
            import json

            payload: dict[str, Any] = json.loads(completed.stdout)
            lines = [
                EngineLine(
                    multipv=int(item.get("multipv", index + 1)),
                    score=item.get("score", 0),
                    pv=list(item.get("pv", [])),
                )
                for index, item in enumerate(payload.get("lines", []))
            ]
        except Exception as exc:
            raise ChessEngineError(f"AlphaZero returned invalid JSON: {exc}") from exc
        if not lines:
            raise ChessEngineError("AlphaZero returned no analysis lines")
        return EngineResult(lines=lines, source="AlphaZero")

    @staticmethod
    def _gpu_available() -> bool:
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False


class Lc0Worker:
    """Leela Chess Zero UCI worker protected by a GPU-aware slot limiter."""

    def __init__(
        self,
        binary_path: str | None = None,
        weights_path: str | None = None,
        max_workers: int | None = None,
        timeout: int | None = None,
    ) -> None:
        configured_binary = binary_path or settings.LC0_BINARY_PATH
        self.binary_path = configured_binary or shutil.which("lc0") or "/usr/games/lc0"
        self.weights_path = weights_path if weights_path is not None else settings.LC0_WEIGHTS_PATH
        self.max_workers = _positive_int(max_workers or settings.LC0_MAX_WORKERS, 1)
        self.timeout = _positive_int(timeout or settings.LC0_TIMEOUT, 60)
        self._slot_limiter = CrossProcessSlotLimiter("lc0", self.max_workers)
        self._active_workers = 0
        self._lock = threading.Lock()

    @property
    def active_workers(self) -> int:
        with self._lock:
            return self._active_workers

    def capability(self) -> EngineCapability:
        binary_exists = bool(self.binary_path and Path(self.binary_path).exists())
        weights_ready = bool(self.weights_path and Path(self.weights_path).exists())
        rocm_ready = self._rocm_available()
        available = binary_exists and weights_ready and rocm_ready

        missing: list[str] = []
        if not binary_exists:
            missing.append(f"LC0 binary at {self.binary_path}")
        if not weights_ready:
            missing.append("LC0_WEIGHTS_PATH")
        if not rocm_ready:
            missing.append("ROCm runtime")

        return EngineCapability(
            key="lc0",
            label="Leela/LC0",
            available=available,
            status="available" if available else "unavailable",
            detail=(
                f"backend={settings.LC0_BACKEND} weights={self.weights_path}"
                if available
                else "Missing " + ", ".join(missing)
            ),
            concurrency_limit=self.max_workers,
            active_workers=self.active_workers,
            binary=self.binary_path,
        )

    def analyze(self, fen: str, depth: int, multipv: int) -> EngineResult:
        capability = self.capability()
        if not capability.available:
            raise ChessEngineError(f"LC0 unavailable: {capability.detail}")

        start = time.time()
        with self._slot_limiter.acquire(timeout=self.timeout):
            with self._lock:
                self._active_workers += 1
            try:
                return self._run_uci(fen=fen, depth=depth, multipv=multipv)
            finally:
                with self._lock:
                    self._active_workers -= 1
                logger.info(
                    "[LC0] request finished in %.3fs active=%s/%s",
                    time.time() - start,
                    self.active_workers,
                    self.max_workers,
                )

    def _run_uci(self, fen: str, depth: int, multipv: int) -> EngineResult:
        bounded_nodes = max(
            1,
            min(int(depth) * settings.LC0_NODES_PER_DEPTH, settings.LC0_MAX_NODES),
        )
        bounded_multipv = max(1, min(int(multipv), settings.LC0_MAX_MULTIPV))
        command = [
            self.binary_path,
            f"--backend={settings.LC0_BACKEND}",
            f"--weights={self.weights_path}",
        ]

        proc = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        assert proc.stdin is not None
        assert proc.stdout is not None

        info_lines: list[str] = []
        try:
            LocalStockfishWorker._send(proc, "uci")
            LocalStockfishWorker._read_until(proc, "uciok", timeout=10)
            LocalStockfishWorker._send(proc, f"setoption name MultiPV value {bounded_multipv}")
            LocalStockfishWorker._send(proc, "isready")
            LocalStockfishWorker._read_until(proc, "readyok", timeout=10)
            LocalStockfishWorker._send(proc, f"position fen {fen}")
            LocalStockfishWorker._send(proc, f"go nodes {bounded_nodes}")

            deadline = time.time() + self.timeout
            while time.time() < deadline:
                line = proc.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith("info "):
                    info_lines.append(line)
                if line.startswith("bestmove"):
                    break

            if time.time() >= deadline:
                raise ChessEngineTimeoutError(self.timeout)

            lines = parse_stockfish_info_lines(info_lines, LocalStockfishWorker._fen_turn(fen))
            if not lines:
                raise ChessEngineError("No usable LC0 analysis lines")
            return EngineResult(lines=lines, source="LC0")
        finally:
            LocalStockfishWorker._send_quit(proc)

    @staticmethod
    def _rocm_available() -> bool:
        try:
            result = subprocess.run(
                ["rocminfo"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = f"{result.stdout}\n{result.stderr}"
            return result.returncode == 0 and ("gfx" in output or "GPU" in output)
        except Exception:
            return False


def parse_stockfish_info_lines(info_lines: list[str], turn: str = "w") -> list[EngineLine]:
    """Parse Stockfish UCI info lines into best lines at the deepest depth."""

    entries: list[tuple[int, int, int | str, list[str]]] = []
    for line in info_lines:
        tokens = line.strip().split()
        try:
            depth_idx = tokens.index("depth")
            score_idx = tokens.index("score")
            pv_idx = tokens.index("pv")
        except ValueError:
            continue

        try:
            depth = int(tokens[depth_idx + 1])
        except (ValueError, IndexError):
            continue

        multipv = 1
        if "multipv" in tokens:
            try:
                multipv_idx = tokens.index("multipv")
                multipv = int(tokens[multipv_idx + 1])
            except (ValueError, IndexError):
                multipv = 1

        score_type = tokens[score_idx + 1] if score_idx + 1 < len(tokens) else None
        score_val = tokens[score_idx + 2] if score_idx + 2 < len(tokens) else None
        pv_moves = tokens[pv_idx + 1 :] if pv_idx + 1 < len(tokens) else []
        if not pv_moves:
            continue

        score: int | str = 0
        if score_type == "cp" and score_val is not None:
            try:
                score = int(score_val)
            except ValueError:
                score = 0
        elif score_type == "mate" and score_val is not None:
            score = f"mate{score_val}"

        entries.append((depth, multipv, _normalize_score_for_white(score, turn), pv_moves))

    if not entries:
        return []

    max_depth = max(depth for depth, _, _, _ in entries)
    per_multipv: dict[int, tuple[int, int | str, list[str]]] = {}
    for depth, multipv, score, pv_moves in entries:
        if depth != max_depth:
            continue
        per_multipv[multipv] = (depth, score, pv_moves)

    if not per_multipv:
        for depth, multipv, score, pv_moves in entries:
            previous = per_multipv.get(multipv)
            if previous is None or depth > previous[0]:
                per_multipv[multipv] = (depth, score, pv_moves)

    return [
        EngineLine(multipv=multipv, score=score, pv=pv_moves)
        for multipv, (_, score, pv_moves) in sorted(per_multipv.items())
    ]


def _normalize_score_for_white(score: int | str, turn: str) -> int | str:
    return score


_stockfish_worker: LocalStockfishWorker | None = None
_alphazero_worker: AlphaZeroWorker | None = None
_lc0_worker: Lc0Worker | None = None


def get_local_stockfish_worker() -> LocalStockfishWorker:
    global _stockfish_worker
    if _stockfish_worker is None:
        _stockfish_worker = LocalStockfishWorker()
    return _stockfish_worker


def get_alphazero_worker() -> AlphaZeroWorker:
    global _alphazero_worker
    if _alphazero_worker is None:
        _alphazero_worker = AlphaZeroWorker()
    return _alphazero_worker


def get_lc0_worker() -> Lc0Worker:
    global _lc0_worker
    if _lc0_worker is None:
        _lc0_worker = Lc0Worker()
    return _lc0_worker


def get_engine_capabilities() -> list[EngineCapability]:
    return [
        get_local_stockfish_worker().capability(),
        get_lc0_worker().capability(),
        get_alphazero_worker().capability(),
    ]
