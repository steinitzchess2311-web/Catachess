import asyncio
import logging
import os
import sys
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.core.config import settings
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.tables.studies import Chapter
from modules.workspace.pgn_v2.repo import PgnV2Repo, validate_chapter_r2_key, backfill_chapter_r2_key
from modules.workspace.storage.r2_client import R2Client
from modules.workspace.domain.services.pgn_sync_service import PgnSyncService
from modules.workspace.storage.keys import R2Keys

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# --- Database Setup ---
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please set it in your environment variables or .env file.")
    sys.exit(1)

engine = create_async_engine(DATABASE_URL, echo=False)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

# --- Main Scan Function ---
async def scan_pgn_integrity():
    logger.info("Starting PGN integrity scan...")

    r2_client = R2Client(
        r2_endpoint=os.getenv("R2_ENDPOINT", ""),
        r2_access_key_id=os.getenv("R2_ACCESS_KEY_ID", ""),
        r2_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY", ""),
        r2_bucket_name=os.getenv("R2_BUCKET_NAME", ""),
    )
    pgn_v2_repo = PgnV2Repo(r2_client)
    
    # Initialize report data
    report: Dict[str, Any] = {
        "scan_timestamp": datetime.now().isoformat(),
        "total_chapters_scanned": 0,
        "r2_key_mismatches": [],
        "r2_missing_pgn": [],
        "r2_missing_tree_json": [],
        "r2_missing_fen_index": [],
        "pgn_hash_mismatches": [],
        "pgn_size_mismatches": [],
        "chapters_repaired": 0,
        "pgn_sync_failures": [],
        "chapters_marked_missing": [], # If pgn_status is added
    }

    async for session in get_session():
        study_repo = StudyRepository(session)
        variation_repo = VariationRepository(session) # Needed by PgnSyncService
        pgn_sync_service = PgnSyncService(study_repo, variation_repo, r2_client)

        chapters = await study_repo.get_all_chapters()
        report["total_chapters_scanned"] = len(chapters)

        for chapter in chapters:
            chapter_id = chapter.id
            logger.info(f"Processing chapter: {chapter_id} - '{chapter.title}'")

            repaired_chapter = False

            # Rule 1: chapter.r2_key != R2Keys.chapter_pgn(chapter_id) -> backfill
            expected_r2_key = R2Keys.chapter_pgn(chapter_id)
            if not validate_chapter_r2_key(chapter, expected_r2_key):
                logger.warning(f"R2 key mismatch for chapter {chapter_id}. Backfilling...")
                chapter.r2_key = backfill_chapter_r2_key(chapter)
                await study_repo.update_chapter(chapter)
                report["r2_key_mismatches"].append(chapter_id)
                repaired_chapter = True

            # Rule 2 & 3: R2 404, hash/size mismatch -> resync PGN
            try:
                pgn_exists = pgn_v2_repo.exists_pgn(chapter_id)
                tree_exists = pgn_v2_repo.exists_tree_json(chapter_id)
                fen_index_exists = pgn_v2_repo.exists_fen_index(chapter_id)
                
                needs_resync = False

                if not pgn_exists:
                    logger.warning(f"R2 PGN missing for chapter {chapter_id}. Needs resync.")
                    report["r2_missing_pgn"].append(chapter_id)
                    # Mark missing logic would go here if pgn_status field existed
                    needs_resync = True
                if not tree_exists:
                    logger.warning(f"R2 Tree JSON missing for chapter {chapter_id}. Needs resync.")
                    report["r2_missing_tree_json"].append(chapter_id)
                    needs_resync = True
                if not fen_index_exists:
                    logger.warning(f"R2 FEN index missing for chapter {chapter_id}. Needs resync.")
                    report["r2_missing_fen_index"].append(chapter_id)
                    needs_resync = True
                
                # Check hash/size mismatch - requires loading and re-calculating, or a better sync mechanism
                # For now, if any R2 artifact is missing, we trigger a resync
                # The sync_chapter_pgn will rebuild and re-upload all artifacts and update chapter metadata

                if needs_resync:
                    logger.info(f"Resyncing chapter {chapter_id} due to missing R2 artifacts...")
                    try:
                        await pgn_sync_service.sync_chapter_pgn(chapter_id)
                        report["chapters_repaired"] += 1
                        repaired_chapter = True
                    except Exception as sync_exc:
                        logger.error(f"Failed to resync PGN for chapter {chapter_id}: {sync_exc}")
                        report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(sync_exc)})
                elif chapter.pgn_hash is None or chapter.pgn_size is None or chapter.r2_etag is None:
                    # If metadata is missing but PGN exists, also resync to populate metadata
                    logger.warning(f"Chapter metadata (hash/size/etag) missing for {chapter_id}. Resyncing...")
                    try:
                        await pgn_sync_service.sync_chapter_pgn(chapter_id)
                        report["chapters_repaired"] += 1
                        repaired_chapter = True
                    except Exception as sync_exc:
                        logger.error(f"Failed to resync PGN for chapter {chapter_id} (metadata): {sync_exc}")
                        report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(sync_exc)})


            except Exception as e:
                logger.error(f"Error checking R2 for chapter {chapter_id}: {e}")
                report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(e)})
            
            if repaired_chapter:
                report["chapters_repaired"] += 1

        await session.commit()
        logger.info("PGN integrity scan completed.")

    # Output report
    print("\n--- PGN Integrity Scan Report ---")
    print(f"Scan Timestamp: {report['scan_timestamp']}")
    print(f"Total Chapters Scanned: {report['total_chapters_scanned']}")
    print(f"R2 Key Mismatches: {len(report['r2_key_mismatches'])}")
    for cid in report['r2_key_mismatches']:
        print(f"  - {cid}")
    print(f"R2 Missing PGN: {len(report['r2_missing_pgn'])}")
    for cid in report['r2_missing_pgn']:
        print(f"  - {cid}")
    print(f"R2 Missing Tree JSON: {len(report['r2_missing_tree_json'])}")
    for cid in report['r2_missing_tree_json']:
        print(f"  - {cid}")
    print(f"R2 Missing FEN Index: {len(report['r2_missing_fen_index'])}")
    for cid in report['r2_missing_fen_index']:
        print(f"  - {cid}")
    print(f"PGN Sync Failures: {len(report['pgn_sync_failures'])}")
    for failure in report['pgn_sync_failures']:
        print(f"  - {failure['chapter_id']}: {failure['error']}")
    print(f"Chapters Repaired (via resync/backfill): {report['chapters_repaired']}")
    print("-----------------------------------")


if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(scan_pgn_integrity())
