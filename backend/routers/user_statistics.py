"""
User Statistics API Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from modules.workspace.db.session import get_session
from core.security.auth import get_current_user_id
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.storage.r2_client import create_r2_client_from_env, R2Client
from services.user_statistics import get_user_statistics, update_user_statistics, increment_online_time


router = APIRouter(prefix="/api/v1/user/statistics", tags=["user-statistics"])


class UserStatisticsResponse(BaseModel):
    """User statistics response"""
    total_online_seconds: int
    total_moves_count: int
    total_online_hours: float


class RecalculateMovesResponse(BaseModel):
    """Response for moves recalculation"""
    success: bool
    total_moves_count: int
    message: str


class HeartbeatResponse(BaseModel):
    """Response for heartbeat"""
    success: bool
    total_online_seconds: int
    message: str


async def get_node_repo(session: AsyncSession = Depends(get_session)) -> NodeRepository:
    """Get node repository dependency"""
    return NodeRepository(session)


async def get_study_repo(session: AsyncSession = Depends(get_session)) -> StudyRepository:
    """Get study repository dependency"""
    return StudyRepository(session)


def get_r2_client() -> R2Client:
    """Get R2 client dependency"""
    return create_r2_client_from_env()


@router.get("", response_model=UserStatisticsResponse)
async def get_current_user_statistics(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Get current user's statistics.

    Returns:
        - total_online_seconds: Total time spent online (seconds)
        - total_moves_count: Total chess moves made across all studies
        - total_online_hours: Total online time in hours (rounded to 1 decimal)
    """
    stats = await get_user_statistics(user_id, session)
    return UserStatisticsResponse(**stats)


@router.post("/recalculate-moves", response_model=RecalculateMovesResponse)
async def recalculate_user_moves(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    study_repo: StudyRepository = Depends(get_study_repo),
    r2_client: R2Client = Depends(get_r2_client)
):
    """
    Recalculate total moves count for current user.

    This endpoint scans all of the user's chapters and counts
    the total number of moves across all studies.

    Returns:
        - success: Whether the recalculation succeeded
        - total_moves_count: Updated total moves count
        - message: Status message
    """
    user = await update_user_statistics(
        user_id=user_id,
        session=session,
        node_repo=node_repo,
        study_repo=study_repo,
        r2_client=r2_client,
        update_moves=True,
        update_online_time=False
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return RecalculateMovesResponse(
        success=True,
        total_moves_count=user.total_moves_count,
        message=f"Successfully recalculated moves count: {user.total_moves_count}"
    )


@router.post("/heartbeat", response_model=HeartbeatResponse)
async def record_heartbeat(
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session)
):
    """
    Record user heartbeat to track online time.

    Frontend should call this endpoint every 60 seconds while user is active.
    Each heartbeat adds 60 seconds to total_online_seconds.

    Returns:
        - success: Whether the heartbeat was recorded
        - total_online_seconds: Updated total online time
        - message: Status message
    """
    success = await increment_online_time(user_id, session, seconds=60)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to record heartbeat")

    # Get updated statistics
    stats = await get_user_statistics(user_id, session)

    return HeartbeatResponse(
        success=True,
        total_online_seconds=stats['total_online_seconds'],
        message="Heartbeat recorded successfully"
    )
