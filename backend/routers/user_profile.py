"""
User Profile Router - User profile and settings endpoints

Endpoints:
    GET /user/profile - Get current user's profile
    PUT /user/profile - Update current user's profile (chess info, self-intro, etc.)

This router handles user profile information that users can set after signup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

from core.db.deps import get_db
from core.security.current_user import get_current_user
from services.user_service import get_user_by_id, update_user_profile
from models.user import User
from core.log.log_api import logger

router = APIRouter(prefix="/user", tags=["user"])


# Request/Response Schemas
class UserProfileResponse(BaseModel):
    """Complete user profile information"""
    id: str
    username: str | None
    identifier: str
    role: str
    is_verified: bool
    created_at: str

    # Chess profile fields
    lichess_username: str | None = None
    chesscom_username: str | None = None
    fide_rating: int | None = None
    cfc_rating: int | None = None
    ecf_rating: int | None = None
    chinese_athlete_title: str | None = None
    fide_title: str | None = None
    self_intro: str | None = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """
    Update user profile request.
    All fields are optional - only provided fields will be updated.
    """
    # Online chess platform usernames
    lichess_username: str | None = Field(None, max_length=50, description="Lichess username")
    chesscom_username: str | None = Field(None, max_length=50, description="Chess.com username")

    # Chess ratings
    fide_rating: int | None = Field(None, ge=0, le=3500, description="FIDE rating (0-3500)")
    cfc_rating: int | None = Field(None, ge=0, le=3500, description="CFC rating (0-3500)")
    ecf_rating: int | None = Field(None, ge=0, le=3500, description="ECF rating (0-3500)")

    # Chess titles
    chinese_athlete_title: str | None = Field(None, max_length=100, description="Chinese athlete title")
    fide_title: str | None = Field(
        None,
        max_length=10,
        description="FIDE title (GM, IM, FM, CM, WGM, WIM, WFM, WCM)"
    )

    # Self introduction
    self_intro: str | None = Field(None, max_length=5000, description="Self introduction")


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's profile.

    Returns complete profile information including chess-related fields.

    Args:
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)

    Returns:
        User profile information

    Raises:
        401: Not authenticated
        404: User not found
    """
    logger.info(f"Profile request: user_id={current_user.id}")

    # Fetch fresh user data from database
    user = get_user_by_id(db, current_user.id)
    if not user:
        logger.error(f"User not found: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserProfileResponse(
        id=str(user.id),
        username=user.username,
        identifier=user.identifier,
        role=user.role,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
        lichess_username=user.lichess_username,
        chesscom_username=user.chesscom_username,
        fide_rating=user.fide_rating,
        cfc_rating=user.cfc_rating,
        ecf_rating=user.ecf_rating,
        chinese_athlete_title=user.chinese_athlete_title,
        fide_title=user.fide_title,
        self_intro=user.self_intro,
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current user's profile.

    Only provided fields will be updated. All fields are optional.
    Users can update their chess-related information and self-introduction.

    Args:
        request: Profile update data
        current_user: Current authenticated user (auto-injected)
        db: Database session (auto-injected)

    Returns:
        Updated user profile information

    Raises:
        401: Not authenticated
        404: User not found
        400: Invalid input data
    """
    logger.info(f"Profile update request: user_id={current_user.id}")

    # Prepare update data (only include fields that were provided)
    update_data = request.model_dump(exclude_unset=True)

    if not update_data:
        logger.info(f"No fields to update for user {current_user.id}")
        # No fields to update, return current profile
        return get_profile(current_user=current_user, db=db)

    logger.info(f"Updating profile fields: {list(update_data.keys())} for user {current_user.id}")

    # Update user profile
    updated_user = update_user_profile(db, current_user.id, update_data)

    if not updated_user:
        logger.error(f"Failed to update profile: user not found {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(f"Profile updated successfully: user_id={current_user.id}")

    return UserProfileResponse(
        id=str(updated_user.id),
        username=updated_user.username,
        identifier=updated_user.identifier,
        role=updated_user.role,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at.isoformat(),
        lichess_username=updated_user.lichess_username,
        chesscom_username=updated_user.chesscom_username,
        fide_rating=updated_user.fide_rating,
        cfc_rating=updated_user.cfc_rating,
        ecf_rating=updated_user.ecf_rating,
        chinese_athlete_title=updated_user.chinese_athlete_title,
        fide_title=updated_user.fide_title,
        self_intro=updated_user.self_intro,
    )
