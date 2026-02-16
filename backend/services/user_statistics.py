"""
User Statistics Service

Handles calculation and updating of user statistics:
- Total online time
- Total moves count
"""

import json
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.storage.r2_client import R2Client
from modules.workspace.storage.keys import R2Keys
from core.log.log_api import logger


async def calculate_user_moves_count(
    user_id: str,
    study_repo: StudyRepository,
    r2_client: R2Client
) -> int:
    """
    Calculate total number of moves across all user's studies.

    Args:
        user_id: User ID
        study_repo: Study repository instance
        r2_client: R2 client instance

    Returns:
        Total number of move nodes
    """
    total_moves = 0

    try:
        # Get all chapters owned by user (via their studies)
        # Note: We need to get studies first, then chapters
        # This is a simplified version - you may need to adjust based on your schema

        # For now, we'll get all chapters and filter by ownership
        # You'll need to implement proper ownership checking
        chapters = await study_repo.get_all_chapters()

        for chapter in chapters:
            try:
                # Load tree from R2
                tree_key = chapter.r2_key or R2Keys.chapter_tree_json(chapter.id)

                if not r2_client.exists(tree_key):
                    continue

                tree_json = r2_client.download_json(tree_key)
                tree = json.loads(tree_json)

                # Count nodes (excluding root)
                if 'nodes' in tree:
                    # Subtract 1 for root node
                    moves_in_chapter = max(0, len(tree['nodes']) - 1)
                    total_moves += moves_in_chapter

            except Exception as e:
                logger.warning(f"Failed to count moves in chapter {chapter.id}: {e}")
                continue

        logger.info(f"Calculated {total_moves} total moves for user {user_id}")
        return total_moves

    except Exception as e:
        logger.error(f"Failed to calculate moves count for user {user_id}: {e}")
        return 0


async def update_user_statistics(
    user_id: str,
    session: AsyncSession,
    study_repo: StudyRepository,
    r2_client: R2Client,
    update_moves: bool = True,
    update_online_time: bool = False,
    online_seconds_to_add: int = 0
) -> Optional[User]:
    """
    Update user statistics.

    Args:
        user_id: User ID
        session: Database session
        study_repo: Study repository instance
        r2_client: R2 client instance
        update_moves: Whether to recalculate moves count
        update_online_time: Whether to update online time
        online_seconds_to_add: Seconds to add to online time

    Returns:
        Updated User object or None if user not found
    """
    try:
        # Get user
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"User {user_id} not found")
            return None

        # Update moves count
        if update_moves:
            total_moves = await calculate_user_moves_count(user_id, study_repo, r2_client)
            user.total_moves_count = total_moves

        # Update online time
        if update_online_time and online_seconds_to_add > 0:
            user.total_online_seconds += online_seconds_to_add

        await session.commit()
        await session.refresh(user)

        logger.info(
            f"Updated statistics for user {user_id}: "
            f"moves={user.total_moves_count}, "
            f"online_seconds={user.total_online_seconds}"
        )

        return user

    except Exception as e:
        logger.error(f"Failed to update statistics for user {user_id}: {e}")
        await session.rollback()
        return None


async def get_user_statistics(user_id: str, session: AsyncSession) -> dict:
    """
    Get user statistics.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        Dictionary with statistics
    """
    try:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {
                'total_online_seconds': 0,
                'total_moves_count': 0,
                'total_online_hours': 0.0
            }

        return {
            'total_online_seconds': user.total_online_seconds,
            'total_moves_count': user.total_moves_count,
            'total_online_hours': round(user.total_online_seconds / 3600, 1)
        }

    except Exception as e:
        logger.error(f"Failed to get statistics for user {user_id}: {e}")
        return {
            'total_online_seconds': 0,
            'total_moves_count': 0,
            'total_online_hours': 0.0
        }
