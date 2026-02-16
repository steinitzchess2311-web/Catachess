"""
FEN/PGN Import/Export API Endpoints

FastAPI routes for importing and exporting chess content.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.db.session import get_session
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from modules.workspace.storage.keys import R2Keys

from ..services.fen_importer import (
    create_chapter_from_fen,
    create_empty_tree,
)
from ..services.fen_validator import is_standard_fen
from .schemas import FenImportRequest, FenImportResponse, ErrorResponse


logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/v1/import-export",
    tags=["import-export"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


# Dependency for StudyRepository
async def get_study_repo(
    session: AsyncSession = Depends(get_session),
) -> StudyRepository:
    """Get StudyRepository instance."""
    return StudyRepository(session)


# Dependency for R2Client
def get_r2_client() -> R2Client:
    """Get R2Client instance."""
    return create_r2_client_from_env()


@router.post(
    "/fen/import",
    response_model=FenImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import FEN position",
    description="""
    Create a new Study Chapter from a FEN (Forsyth-Edwards Notation) position.

    This endpoint allows you to start a chapter from any custom chess position,
    such as endgames, puzzles, or specific middlegame positions.

    The chapter will be created with an empty tree (only root node), and you can
    then add moves manually.

    **Use Cases:**
    - 🏁 Endgame practice (e.g., King+Queen vs King)
    - 🧩 Puzzle analysis from specific positions
    - 📚 Middlegame training
    - 🎲 Chess960 starting positions

    **FEN Format:**
    FEN strings must include at least 4 parts:
    - Piece placement (e.g., "rnbqkbnr/pppppppp/...")
    - Active color ("w" or "b")
    - Castling availability (e.g., "KQkq" or "-")
    - En passant target square (e.g., "e3" or "-")

    Optional parts (will be auto-filled if missing):
    - Halfmove clock (default: 0)
    - Fullmove number (default: 1)

    **Standard Position Optimization:**
    If the FEN represents the standard starting position, `starting_fen` will be
    stored as NULL in the database to save space.
    """,
)
async def import_from_fen(
    request: FenImportRequest,
    study_repo: StudyRepository = Depends(get_study_repo),
    r2_client: R2Client = Depends(get_r2_client),
) -> FenImportResponse:
    """
    Import FEN position and create a new chapter.

    Args:
        request: FEN import request containing study_id, chapter_title, and fen
        study_repo: StudyRepository instance
        r2_client: R2Client instance

    Returns:
        FenImportResponse with created chapter details

    Raises:
        HTTPException 404: Study not found
        HTTPException 400: Invalid FEN or other validation error
        HTTPException 500: Internal server error
    """
    try:
        # 1. Verify study exists
        study = await study_repo.get_study_by_id(request.study_id)
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Study not found: {request.study_id}"
            )

        # 2. Get next chapter order
        chapters = await study_repo.get_chapters_for_study(request.study_id)
        next_order = len(chapters)

        # 3. Create chapter from FEN
        chapter = create_chapter_from_fen(
            study_id=request.study_id,
            chapter_title=request.chapter_title,
            fen=request.fen,  # Already validated by Pydantic
            order=next_order
        )

        # 4. Create empty tree
        tree = create_empty_tree()

        # 5. Upload tree to R2
        import json
        tree_json = json.dumps(tree)
        upload_result = r2_client.upload_json(
            key=R2Keys.chapter_tree_json(chapter.id),
            content=tree_json
        )
        chapter.r2_etag = upload_result.etag

        # 6. Save chapter to database
        await study_repo.create_chapter(chapter)

        # 7. Update study chapter count
        await study_repo.update_chapter_count(request.study_id)

        logger.info(
            f"Created chapter {chapter.id} from FEN in study {request.study_id}",
            extra={
                "chapter_id": chapter.id,
                "study_id": request.study_id,
                "is_standard_position": is_standard_fen(request.fen)
            }
        )

        return FenImportResponse(
            chapter_id=chapter.id,
            starting_fen=chapter.starting_fen,
            message="Chapter created successfully from FEN position"
        )

    except ValueError as e:
        # FEN validation errors
        logger.warning(f"FEN validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in FEN import: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while importing FEN"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the import/export service is running",
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "pgn_fen_import_export",
        "version": "0.1.0"
    }
