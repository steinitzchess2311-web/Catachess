"""
Imitator Router

Ranks candidate moves by player profile similarity.
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from core.tagger.pipeline.predictor.predictor import predict_moves, PROFILES_DIR
from core.tagger.pipeline.predictor.profile_loader import list_profiles

router = APIRouter(prefix="/api/imitator", tags=["imitator"])


class ImitatorRequest(BaseModel):
    fen: str
    player: str
    depth: int = 12
    multipv: int = 8
    top_n: int = 3


class ImitatorMove(BaseModel):
    move: str
    engine_eval: int | str
    similarity: float
    probability: float


class ImitatorResponse(BaseModel):
    player: str
    moves: list[ImitatorMove]


@router.get("/profiles")
async def get_profiles():
    return {"profiles": list_profiles(PROFILES_DIR)}


@router.post("/predict", response_model=ImitatorResponse)
async def predict(request: ImitatorRequest):
    profile_path = Path(PROFILES_DIR) / f"{request.player}.csv"
    if not profile_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{request.player}' not found",
        )
    try:
        result = predict_moves(
            fen=request.fen,
            profile_name=request.player,
            depth=request.depth,
            multipv=request.multipv,
            top_n=request.top_n,
        )
        return {
            "player": result["profile_name"],
            "moves": result["moves"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )
