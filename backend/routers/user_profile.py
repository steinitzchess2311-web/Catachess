"""
User Profile Router - User profile and settings endpoints

Endpoints:
    GET /user/profile - Get current user's profile
    PUT /user/profile - Update current user's profile (chess info, self-intro, etc.)
    GET /user/by-username/{username} - Look up a user by username (for catachat)

This router handles user profile information that users can set after signup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, Field
import uuid

from core.db.deps import get_db
from core.security.current_user import get_current_user
from services.user_service import get_user_by_id, get_user_by_username, update_user_profile
from models.user import User
from core.log.log_api import logger

router = APIRouter(prefix="/user", tags=["user"])

CHINESE_CHESS_ASSOCIATION_TITLE_VALUES = ("三运", "二运", "一运", "候补", "棋协")
CHINESE_TITLE_ALIASES = {
    "三运": "三运",
    "三级运动员": "三运",
    "国家三级运动员": "三运",
    "二运": "二运",
    "二级运动员": "二运",
    "国家二级运动员": "二运",
    "一运": "一运",
    "一级运动员": "一运",
    "国家一级运动员": "一运",
    "候补": "候补",
    "候补棋协大师": "候补",
    "棋协": "棋协",
    "棋协大师": "棋协",
    "中国棋协大师": "棋协",
}


def normalize_chinese_chess_association_title(value: str | None) -> str | None:
    """Return the approved short Chinese Chess Association title, or None."""
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return CHINESE_TITLE_ALIASES.get(stripped)


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
    chinese_athlete_title: str | None = Field(None, max_length=20, description="Chinese Chess Association title")
    fide_title: str | None = Field(
        None,
        max_length=10,
        description="FIDE title (GM, IM, FM, CM, WGM, WIM, WFM, WCM)"
    )

    # Self introduction
    self_intro: str | None = Field(None, max_length=5000, description="Self introduction")


class PublicProfileResponse(BaseModel):
    """公开资料——不含敏感字段（identifier、role、is_verified 等）"""
    username: str
    fide_title: str | None = None
    fide_rating: int | None = None
    cfc_rating: int | None = None
    ecf_rating: int | None = None
    chinese_athlete_title: str | None = None
    lichess_username: str | None = None
    chesscom_username: str | None = None
    self_intro: str | None = None

    class Config:
        from_attributes = True


class UserLookupResponse(BaseModel):
    """Minimal user info for starting a catachat conversation."""
    id: str
    username: str


@router.get("/by-username/{username}", response_model=UserLookupResponse)
def lookup_user_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Look up a user by their username. Used by catachat to find who to message."""
    user = db.execute(
        select(User).where(User.username == username)
    ).scalar_one_or_none()
    if not user or not user.username:
        raise HTTPException(status_code=404, detail="User not found")
    return UserLookupResponse(id=str(user.id), username=user.username)


@router.get("/profile/{username}", response_model=PublicProfileResponse)
def get_public_profile(
    username: str,
    db: Session = Depends(get_db),
):
    """
    获取指定用户的公开资料（无需登录）。

    任何人都可以访问，不含敏感字段（identifier、role 等）。
    用于 /@username 个人主页展示。

    Args:
        username: 要查询的用户名
        db: 数据库会话（自动注入）

    Returns:
        PublicProfileResponse — 公开可见的棋手信息

    Raises:
        404: 用户不存在
    """
    logger.info(f"Public profile request: username={username}")

    user = get_user_by_username(db, username)
    if not user:
        logger.info(f"Public profile not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    logger.info(f"Public profile returned: {user.username}")
    return PublicProfileResponse(
        username=user.username,
        fide_title=user.fide_title,
        fide_rating=user.fide_rating,
        cfc_rating=user.cfc_rating,
        ecf_rating=user.ecf_rating,
        chinese_athlete_title=normalize_chinese_chess_association_title(user.chinese_athlete_title),
        lichess_username=user.lichess_username,
        chesscom_username=user.chesscom_username,
        self_intro=user.self_intro,
    )


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
        chinese_athlete_title=normalize_chinese_chess_association_title(user.chinese_athlete_title),
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
    if "chinese_athlete_title" in update_data:
        raw_chinese_title = update_data["chinese_athlete_title"]
        normalized_title = normalize_chinese_chess_association_title(
            raw_chinese_title
        )
        if raw_chinese_title and raw_chinese_title.strip() and normalized_title is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chinese Chess Association title must be one of: {', '.join(CHINESE_CHESS_ASSOCIATION_TITLE_VALUES)}",
            )
        update_data["chinese_athlete_title"] = normalized_title

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
        chinese_athlete_title=normalize_chinese_chess_association_title(updated_user.chinese_athlete_title),
        fide_title=updated_user.fide_title,
        self_intro=updated_user.self_intro,
    )
