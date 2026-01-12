"""
API Schemas package
"""
from schemas.game import (
    SaveMoveRequest,
    SaveMoveResponse,
    StartVariationRequest,
    EndVariationRequest,
    AddCommentRequest,
    AddNAGRequest,
    VariationResponse,
    CommentResponse,
    PGNResponse,
    GameInfoResponse,
    DeleteGameResponse,
)

__all__ = [
    "SaveMoveRequest",
    "SaveMoveResponse",
    "StartVariationRequest",
    "EndVariationRequest",
    "AddCommentRequest",
    "AddNAGRequest",
    "VariationResponse",
    "CommentResponse",
    "PGNResponse",
    "GameInfoResponse",
    "DeleteGameResponse",
]
