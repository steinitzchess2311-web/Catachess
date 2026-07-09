"""
Created at: 2026-07-08 23:25 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Last Modified by: Codex

Human move predictor API for Maia and Catie providers.
"""

from __future__ import annotations

import json
import subprocess
import asyncio
import time
from pathlib import Path
from typing import Literal

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.chess_engine.local_workers import CrossProcessSlotLimiter
from core.config import settings
from core.log.log_chess_engine import logger
from core.security.rate_limiter import rate_limit


PredictorProvider = Literal["maia", "catie"]

router = APIRouter(prefix="/api/predictor", tags=["predictor"])


class PredictorRequest(BaseModel):
    fen: str
    provider: PredictorProvider = "maia"
    top_k: int = Field(default=5, ge=1, le=10)
    elo: int = Field(default=1500, ge=100, le=4000)


class PredictorMove(BaseModel):
    rank: int
    move: str
    uci: str | None = None
    san: str | None = None
    probability: float
    source: str | None = None


class PredictorResponse(BaseModel):
    provider: PredictorProvider
    model: str
    fen: str
    moves: list[PredictorMove]
    meta: dict = Field(default_factory=dict)


class PredictorHealthResponse(BaseModel):
    providers: list[dict]


def _rate_limit_dependency():
    return rate_limit(limit=settings.PREDICTOR_RATE_LIMIT_PER_MINUTE, window_seconds=60)


@router.get("/health", response_model=PredictorHealthResponse)
async def predictor_health() -> PredictorHealthResponse:
    maia_script = Path(settings.MAIA_SCRIPT_PATH)
    maia_python = Path(settings.MAIA_PYTHON)
    catie_health = await asyncio.to_thread(_catie_health_snapshot)
    return PredictorHealthResponse(
        providers=[
            {
                "key": "maia",
                "label": "Maia",
                "available": maia_script.exists() and maia_python.exists(),
                "detail": f"{settings.MAIA_MODEL_TYPE} via {settings.MAIA_SCRIPT_PATH}",
                "concurrency_limit": settings.MAIA_MAX_WORKERS,
            },
            {
                "key": "catie",
                "label": "Catie",
                "available": bool(catie_health.get("healthy")),
                "detail": catie_health.get("reason") or "local CatieChess model API",
                "base_url": settings.CATIE_MODEL_BASE_URL,
            },
        ]
    )


@router.post(
    "/predict",
    response_model=PredictorResponse,
    dependencies=[Depends(_rate_limit_dependency())],
)
async def predict(request: PredictorRequest) -> PredictorResponse:
    try:
        if request.provider == "maia":
            return await asyncio.to_thread(_predict_maia, request)
        if request.provider == "catie":
            return await asyncio.to_thread(_predict_catie, request)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[PREDICTOR] request failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Predictor unavailable: {exc}",
        ) from exc
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported provider")


def _predict_maia(request: PredictorRequest) -> PredictorResponse:
    script = Path(settings.MAIA_SCRIPT_PATH)
    python = Path(settings.MAIA_PYTHON)
    if not script.exists() or not python.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Maia runtime is not installed on this server",
        )

    limiter = CrossProcessSlotLimiter("predictor-maia", settings.MAIA_MAX_WORKERS)
    command = [
        str(python),
        str(script),
        "--model-type",
        settings.MAIA_MODEL_TYPE,
        "--device",
        settings.MAIA_DEVICE,
        "--fen",
        request.fen,
        "--elo-self",
        str(request.elo),
        "--elo-oppo",
        str(request.elo),
        "--top-k",
        str(request.top_k),
    ]
    with limiter.acquire(timeout=settings.MAIA_TIMEOUT):
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=settings.MAIA_TIMEOUT,
        )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        raise RuntimeError(f"Maia failed: {stderr[:500]}")
    payload = json.loads(completed.stdout)
    moves = [
        PredictorMove(
            rank=index + 1,
            move=item.get("move", ""),
            uci=item.get("move"),
            probability=float(item.get("prob", 0.0)),
            source="maia2",
        )
        for index, item in enumerate(payload.get("top_moves", []))
        if item.get("move")
    ]
    return PredictorResponse(
        provider="maia",
        model=f"maia2-{payload.get('model_type', settings.MAIA_MODEL_TYPE)}",
        fen=request.fen,
        moves=moves,
        meta={
            "elo": request.elo,
            "device": payload.get("device", settings.MAIA_DEVICE),
            "win_prob": payload.get("win_prob"),
        },
    )


def _predict_catie(request: PredictorRequest) -> PredictorResponse:
    create_url = f"{settings.CATIE_MODEL_BASE_URL.rstrip('/')}/api/model/probe-position"
    poll_base = f"{settings.CATIE_MODEL_BASE_URL.rstrip('/')}/api/model/tasks"
    payload = {
        "model_id": settings.CATIE_MODEL_ID,
        "fen": request.fen,
        "top_k": request.top_k,
        "temperature": 0.0,
        "prefix": "bullet",
        "elo": request.elo or settings.CATIE_DEFAULT_ELO,
        "include_policy": True,
        "include_outcome": False,
        "meta": {"source": "catachess_predictor"},
    }
    create_resp = requests.post(create_url, json=payload, timeout=5)
    if create_resp.status_code >= 500:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Catie model API unavailable: {create_resp.text[:300]}",
        )
    create_resp.raise_for_status()
    task_id = create_resp.json().get("task_id")
    if not task_id:
        raise RuntimeError("Catie model API did not return task_id")

    deadline = time.time() + settings.CATIE_POLL_TIMEOUT
    last_payload = None
    while time.time() < deadline:
        poll_resp = requests.get(f"{poll_base}/{task_id}", timeout=5)
        poll_resp.raise_for_status()
        last_payload = poll_resp.json()
        status_value = last_payload.get("status")
        if status_value == "succeeded":
            result = last_payload.get("result") or {}
            policy = result.get("policy") or {}
            top_moves = policy.get("top_k") or []
            moves = [
                PredictorMove(
                    rank=int(item.get("rank", index + 1)),
                    move=item.get("san") or item.get("uci") or "",
                    uci=item.get("uci"),
                    san=item.get("san"),
                    probability=float(item.get("probability", 0.0)),
                    source="catie",
                )
                for index, item in enumerate(top_moves)
            ]
            return PredictorResponse(
                provider="catie",
                model=result.get("model_id") or settings.CATIE_MODEL_ID,
                fen=request.fen,
                moves=moves,
                meta={
                    "task_id": task_id,
                    "runtime_backend": result.get("runtime_backend"),
                    "effective_elo": policy.get("effective_elo"),
                },
            )
        if status_value in {"failed", "cancelled", "expired"}:
            raise RuntimeError(f"Catie task {status_value}: {last_payload.get('error')}")
        time.sleep(settings.CATIE_POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"Catie task timed out: {task_id} last={last_payload}")


def _catie_health_snapshot() -> dict:
    try:
        resp = requests.get(
            f"{settings.CATIE_MODEL_BASE_URL.rstrip('/')}/api/model/health",
            timeout=3,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        return {"healthy": False, "reason": str(exc)}
