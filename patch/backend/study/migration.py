import logging
import asyncio
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from modules.workspace.db.tables.studies import Chapter
from modules.workspace.storage.r2_client import R2Client, create_r2_client_from_env
from modules.workspace.storage.keys import R2Keys
from backend.core.real_pgn.parser import parse_pgn
from backend.core.real_pgn.models import NodeTree
from patch.backend.study.models import StudyTreeDTO, StudyNodeDTO, TreeMetaDTO
from patch.backend.study.converter import convert_nodetree_to_dto

logger = logging.getLogger(__name__)

async def migrate_all_chapters(session: AsyncSession, batch_size: int = 10):
    """
    Migrate all chapters with .pgn r2_key to .tree.json.
    """
    r2_client = create_r2_client_from_env()
    
    # Fetch chapters that need migration
    # Heuristic: r2_key ends with .pgn or is null (implies standard pgn key)
    # We can fetch all and filter in memory if dataset is small, or page.
    # For now, let's just fetch all chapters.
    
    stmt = select(Chapter)
    result = await session.execute(stmt)
    chapters = result.scalars().all()
    
    migrated_count = 0
    error_count = 0
    
    for chapter in chapters:
        try:
            current_key = chapter.r2_key or R2Keys.chapter_pgn(chapter.id)
            
            # Skip if already migrated
            if current_key.endswith(".json"):
                continue
                
            logger.info(f"Migrating chapter {chapter.id} ({current_key})...")
            
            # 1. Download PGN
            if not r2_client.exists(current_key):
                logger.warning(f"PGN not found for chapter {chapter.id} at {current_key}, skipping.")
                continue
                
            pgn_text = r2_client.download_pgn(current_key)
            
            # 2. Parse PGN to NodeTree
            # parse_pgn returns a NodeTree
            node_tree = parse_pgn(pgn_text)
            
            # 3. Convert NodeTree to StudyTreeDTO
            study_tree_dto = convert_nodetree_to_dto(node_tree)
            
            # 4. Upload Tree JSON
            new_key = R2Keys.chapter_tree_json(chapter.id)
            content = study_tree_dto.model_dump_json()
            upload_result = r2_client.upload_json(new_key, content)
            
            # 5. Update Chapter
            chapter.r2_key = new_key
            chapter.pgn_hash = upload_result.content_hash
            chapter.pgn_size = upload_result.size
            chapter.r2_etag = upload_result.etag
            
            # Session commit happens outside or per batch?
            # Let's commit per chapter for safety in this script
            await session.commit()
            
            migrated_count += 1
            logger.info(f"Successfully migrated chapter {chapter.id}")
            
        except Exception as e:
            logger.error(f"Failed to migrate chapter {chapter.id}: {e}")
            error_count += 1
            
    logger.info(f"Migration complete. Migrated: {migrated_count}, Errors: {error_count}")
