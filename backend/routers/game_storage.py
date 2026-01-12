"""
Game Storage Router

8 API endpoints for game storage with PGN and variations.

IMPORTANT: All chess logic is handled in the service layer.
Frontend only triggers events through these endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db.database import get_db
from core.auth import get_current_user
from models.user import User
from schemas.game import (
    SaveMoveRequest,
    SaveMoveResponse,
    StartVariationRequest,
    EndVariationRequest,
    VariationResponse,
    AddCommentRequest,
    AddNAGRequest,
    CommentResponse,
    PGNResponse,
    GameInfoResponse,
    DeleteGameResponse,
)
from services.game_storage_service import game_storage_service


router = APIRouter(
    prefix="/api/games",
    tags=["games"],
)


@router.post("/save-move", response_model=SaveMoveResponse)
async def save_move(
    request: SaveMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save a move to the game

    This endpoint:
    1. Validates the move using backend chess rules
    2. Applies the move to update game state
    3. Generates/updates PGN using PGNWriterVari
    4. Stores PGN to R2
    5. Updates database record

    Frontend only needs to send move data, all logic is here.
    """
    try:
        success, move_id, pgn_preview = game_storage_service.save_move(
            game_id=request.game_id,
            user_id=str(current_user.id),
            move_data=request.move.dict(),
            position_fen=request.position_fen,
            is_variation=request.is_variation,
            parent_move_id=request.parent_move_id,
            comment=request.comment,
            nag=request.nag,
            move_number=request.move_number,
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid move"
            )

        return SaveMoveResponse(
            success=True,
            move_id=move_id,
            pgn_preview=pgn_preview,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save move: {str(e)}"
        )


@router.post("/start-variation", response_model=VariationResponse)
async def start_variation(
    request: StartVariationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a new variation branch

    Call this before adding moves to a variation.
    Backend handles the variation stack using PGNWriterVari.
    """
    try:
        variation_id = game_storage_service.start_variation(
            game_id=request.game_id,
            user_id=str(current_user.id),
            db=db,
        )

        return VariationResponse(
            success=True,
            variation_id=variation_id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start variation: {str(e)}"
        )


@router.post("/end-variation", response_model=VariationResponse)
async def end_variation(
    request: EndVariationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    End current variation branch

    Call this after adding all moves in a variation.
    Returns to the mainline.
    """
    try:
        game_storage_service.end_variation(
            game_id=request.game_id,
            user_id=str(current_user.id),
            db=db,
        )

        return VariationResponse(success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end variation: {str(e)}"
        )


@router.post("/add-comment", response_model=CommentResponse)
async def add_comment(
    request: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add comment to a move

    If move_id is not provided, adds comment to last move.
    """
    try:
        game_storage_service.add_comment(
            game_id=request.game_id,
            user_id=str(current_user.id),
            comment=request.comment,
            db=db,
        )

        return CommentResponse(success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.post("/add-nag", response_model=CommentResponse)
async def add_nag(
    request: AddNAGRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add NAG (Numeric Annotation Glyph) to a move

    Common NAGs:
    - 1: ! (good move)
    - 2: ? (mistake)
    - 3: !! (brilliant move)
    - 4: ?? (blunder)
    - 5: !? (interesting move)
    - 6: ?! (dubious move)

    If move_id is not provided, adds NAG to last move.
    """
    try:
        game_storage_service.add_nag(
            game_id=request.game_id,
            user_id=str(current_user.id),
            nag=request.nag,
            db=db,
        )

        return CommentResponse(success=True)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add NAG: {str(e)}"
        )


@router.get("/{game_id}/pgn", response_model=PGNResponse)
async def get_pgn(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get full PGN for a game

    Returns complete PGN string including:
    - Headers/tags
    - Move text with variations
    - Comments and NAGs
    """
    try:
        pgn, move_count = game_storage_service.get_pgn(
            game_id=game_id,
            user_id=str(current_user.id),
            db=db,
        )

        return PGNResponse(
            pgn=pgn,
            game_id=game_id,
            move_count=move_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get PGN: {str(e)}"
        )


@router.get("/{game_id}", response_model=GameInfoResponse)
async def get_game(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get complete game information

    Returns:
    - Full PGN
    - Move count
    - Current position FEN
    - Player names
    - Result
    - Timestamps
    """
    try:
        game_info = game_storage_service.get_game_info(
            game_id=game_id,
            user_id=str(current_user.id),
            db=db,
        )

        if not game_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )

        return GameInfoResponse(**game_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get game: {str(e)}"
        )


@router.delete("/{game_id}", response_model=DeleteGameResponse)
async def delete_game(
    game_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a game

    Deletes:
    - Game metadata from PostgreSQL
    - PGN file from R2 storage
    - In-memory session cache
    """
    try:
        success = game_storage_service.delete_game(
            game_id=game_id,
            user_id=str(current_user.id),
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )

        return DeleteGameResponse(success=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete game: {str(e)}"
        )
