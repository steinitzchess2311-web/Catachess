import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from backend.core.config import settings
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.repos.variation_repo import VariationRepository
from modules.workspace.db.tables.studies import Chapter
from modules.workspace.pgn_v2.repo import PgnV2Repo, validate_chapter_r2_key, backfill_chapter_r2_key
from modules.workspace.storage.r2_client import R2Client, R2Config
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

# --- Report Output ---
REPORT_DIR = Path("docs/migration_reports")
REPORT_PATH = REPORT_DIR / "migration_scan_report.txt"
SUMMARY_PATH = REPORT_DIR / "migration_scan_summary.json"
ACCEPTANCE_PATH = REPORT_DIR / "migration_acceptance.md"

PGN_STATUS_READY = "ready"
PGN_STATUS_ERROR = "error"
PGN_STATUS_MISSING = "missing"
PGN_STATUS_MISMATCH = "mismatch"


def _resolve_operator() -> str:
    return os.getenv("PGN_SCAN_OPERATOR") or os.getenv("USER") or "unknown"


def _resolve_environment() -> str:
    return os.getenv("ENV") or settings.ENV


def _write_report_files(report: Dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "PGN Integrity Scan Report",
        f"Scan Timestamp: {report['scan_timestamp']}",
        f"Operator: {report['operator']}",
        f"Environment: {report['environment']}",
        f"Host: {report['scan_host']}",
        f"Total Chapters Scanned: {report['total_chapters_scanned']}",
        f"Chapters Without Moves: {len(report['chapters_without_moves'])}",
    ]
    for cid in report["chapters_without_moves"]:
        lines.append(f"  - {cid}")
    lines.append(f"R2 Key Mismatches: {len(report['r2_key_mismatches'])}")
    for cid in report["r2_key_mismatches"]:
        lines.append(f"  - {cid}")
    lines.append(f"R2 Missing PGN: {len(report['r2_missing_pgn'])}")
    for cid in report["r2_missing_pgn"]:
        lines.append(f"  - {cid}")
    lines.append(f"R2 Missing Tree JSON: {len(report['r2_missing_tree_json'])}")
    for cid in report["r2_missing_tree_json"]:
        lines.append(f"  - {cid}")
    lines.append(f"R2 Missing FEN Index: {len(report['r2_missing_fen_index'])}")
    for cid in report["r2_missing_fen_index"]:
        lines.append(f"  - {cid}")
    lines.append(f"PGN Sync Failures: {len(report['pgn_sync_failures'])}")
    for failure in report["pgn_sync_failures"]:
        lines.append(f"  - {failure['chapter_id']}: {failure['error']}")
    lines.append(f"Resync Attempts: {report['resync_attempts']}")
    lines.append(f"Resync Success: {report['resync_success']}")
    lines.append(f"Resync Failures: {report['resync_failures']}")
    lines.append(f"Chapters Repaired (via resync): {report['chapters_repaired']}")
    lines.append("PGN Status Updates:")
    for status_key, ids in report["pgn_status_updates"].items():
        lines.append(f"  - {status_key}: {len(ids)}")
        for cid in ids:
            lines.append(f"    - {cid}")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "scan_timestamp": report["scan_timestamp"],
        "operator": report["operator"],
        "environment": report["environment"],
        "scan_host": report["scan_host"],
        "total_chapters_scanned": report["total_chapters_scanned"],
        "chapters_without_moves": len(report["chapters_without_moves"]),
        "r2_key_mismatches": len(report["r2_key_mismatches"]),
        "r2_missing_pgn": len(report["r2_missing_pgn"]),
        "r2_missing_tree_json": len(report["r2_missing_tree_json"]),
        "r2_missing_fen_index": len(report["r2_missing_fen_index"]),
        "pgn_sync_failures": len(report["pgn_sync_failures"]),
        "chapters_repaired": report["chapters_repaired"],
        "resync_attempts": report["resync_attempts"],
        "resync_success": report["resync_success"],
        "resync_failures": report["resync_failures"],
        "pgn_status_updates": {
            key: len(ids) for key, ids in report["pgn_status_updates"].items()
        },
        "source_report": str(REPORT_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    command = os.getenv("PGN_SCAN_COMMAND") or "PYTHONPATH=.:backend DATABASE_URL=<asyncpg> R2_* .venv/bin/python backend/scripts/scan_pgn_integrity.py"
    acceptance_lines = [
        "# Stage 3B Migration Acceptance Record",
        "",
        "## Execution summary",
        f"- Scan command: `{command}`",
        f"- Output: `{REPORT_PATH}`",
        f"- Execution date: {report['scan_timestamp']}",
        f"- Operator: {report['operator']}",
        f"- Environment: {report['environment']}",
        f"- Host: {report['scan_host']}",
        f"- Total chapters scanned: {report['total_chapters_scanned']}",
        f"- Chapters without moves: {len(report['chapters_without_moves'])}",
        f"- R2 key mismatches: {len(report['r2_key_mismatches'])}",
        f"- R2 missing PGN: {len(report['r2_missing_pgn'])}",
        f"- R2 missing tree JSON: {len(report['r2_missing_tree_json'])}",
        f"- R2 missing FEN index: {len(report['r2_missing_fen_index'])}",
        f"- PGN sync failures: {len(report['pgn_sync_failures'])}",
        f"- Resync attempts: {report['resync_attempts']}",
        f"- Resync success: {report['resync_success']}",
        f"- Resync failures: {report['resync_failures']}",
        f"- Chapters repaired (via resync): {report['chapters_repaired']}",
        "",
        "## PGN status updates",
        f"- ready: {len(report['pgn_status_updates']['ready'])}",
        f"- missing: {len(report['pgn_status_updates']['missing'])}",
        f"- mismatch: {len(report['pgn_status_updates']['mismatch'])}",
        f"- error: {len(report['pgn_status_updates']['error'])}",
        "",
        "## Acceptance status",
        "- Pending manual review of scan output.",
    ]
    ACCEPTANCE_PATH.write_text("\n".join(acceptance_lines) + "\n", encoding="utf-8")


# --- Main Scan Function ---
async def scan_pgn_integrity():
    logger.info("Starting PGN integrity scan...")
    logger.info(f"PGN_V2_ENABLED={settings.PGN_V2_ENABLED}")

    r2_config = R2Config(
        endpoint=os.getenv("R2_ENDPOINT", ""),
        access_key=os.getenv("R2_ACCESS_KEY_ID", ""),
        secret_key=os.getenv("R2_SECRET_ACCESS_KEY", ""),
        bucket=os.getenv("R2_BUCKET_NAME", ""),
    )
    r2_client = R2Client(r2_config)
    pgn_v2_repo = PgnV2Repo(r2_client)
    
    # Initialize report data
    report: Dict[str, Any] = {
        "scan_timestamp": datetime.now().isoformat(),
        "operator": _resolve_operator(),
        "environment": _resolve_environment(),
        "scan_host": os.getenv("HOSTNAME") or "",
        "total_chapters_scanned": 0,
        "chapters_without_moves": [],
        "r2_key_mismatches": [],
        "r2_missing_pgn": [],
        "r2_missing_tree_json": [],
        "r2_missing_fen_index": [],
        "pgn_hash_mismatches": [],
        "pgn_size_mismatches": [],
        "chapters_repaired": 0,
        "resync_attempts": 0,
        "resync_success": 0,
        "resync_failures": 0,
        "pgn_sync_failures": [],
        "pgn_status_updates": {
            PGN_STATUS_READY: [],
            PGN_STATUS_MISSING: [],
            PGN_STATUS_MISMATCH: [],
            PGN_STATUS_ERROR: [],
        },
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
            mismatch_detected = False

            # Rule 1: chapter.r2_key != R2Keys.chapter_pgn(chapter_id) -> backfill
            expected_r2_key = R2Keys.chapter_pgn(chapter_id)
            if not validate_chapter_r2_key(chapter, expected_r2_key):
                logger.warning(f"R2 key mismatch for chapter {chapter_id}. Backfilling...")
                chapter.r2_key = backfill_chapter_r2_key(chapter)
                await study_repo.update_chapter(chapter)
                report["r2_key_mismatches"].append(chapter_id)
                mismatch_detected = True
                chapter.pgn_status = PGN_STATUS_MISMATCH
                await study_repo.update_chapter(chapter)
                report["pgn_status_updates"][PGN_STATUS_MISMATCH].append(chapter_id)

            # Check if chapter has any moves (variations)
            has_moves = True
            try:
                chapter_variations = await variation_repo.get_variations_for_chapter(chapter_id)
                if not chapter_variations:
                    has_moves = False
                    report["chapters_without_moves"].append(chapter_id)
            except Exception as e:
                logger.error(f"Error loading variations for chapter {chapter_id}: {e}")

            # Rule 2 & 3: R2 404, hash/size mismatch -> resync PGN
            # NOTE: Chapters without moves do NOT require R2 artifacts (PGN/tree/fen_index)
            try:
                # For chapters without moves, all R2 checks are skipped (artifacts not required)
                pgn_exists = pgn_v2_repo.exists_pgn(chapter_id) if has_moves else True
                tree_exists = pgn_v2_repo.exists_tree_json(chapter_id) if has_moves else True
                fen_index_exists = pgn_v2_repo.exists_fen_index(chapter_id) if has_moves else True

                needs_resync = False
                missing_detected = False

                if not pgn_exists:
                    logger.warning(f"R2 PGN missing for chapter {chapter_id}. Needs resync.")
                    needs_resync = True
                    missing_detected = True
                if not tree_exists:
                    logger.warning(f"R2 Tree JSON missing for chapter {chapter_id}. Needs resync.")
                    needs_resync = True
                    missing_detected = True
                if not fen_index_exists:
                    logger.warning(f"R2 FEN index missing for chapter {chapter_id}. Needs resync.")
                    needs_resync = True
                    missing_detected = True

                if missing_detected:
                    chapter.pgn_status = PGN_STATUS_MISSING
                    await study_repo.update_chapter(chapter)
                    report["pgn_status_updates"][PGN_STATUS_MISSING].append(chapter_id)
                
                # Check hash/size mismatch - requires loading and re-calculating, or a better sync mechanism
                # For now, if any R2 artifact is missing, we trigger a resync
                # The sync_chapter_pgn will rebuild and re-upload all artifacts and update chapter metadata

                if needs_resync or mismatch_detected:
                    logger.info(
                        f"Resyncing chapter {chapter_id} due to missing R2 artifacts or r2_key mismatch..."
                    )
                    report["resync_attempts"] += 1
                    try:
                        await pgn_sync_service.sync_chapter_pgn(chapter_id)
                        report["resync_success"] += 1
                        chapter = await study_repo.get_chapter_by_id(chapter_id)
                        if chapter:
                            chapter.pgn_status = PGN_STATUS_READY
                            await study_repo.update_chapter(chapter)
                            report["pgn_status_updates"][PGN_STATUS_READY].append(chapter_id)
                        repaired_chapter = True
                    except Exception as sync_exc:
                        logger.error(f"Failed to resync PGN for chapter {chapter_id}: {sync_exc}")
                        report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(sync_exc)})
                        report["resync_failures"] += 1
                        chapter.pgn_status = PGN_STATUS_ERROR
                        await study_repo.update_chapter(chapter)
                        report["pgn_status_updates"][PGN_STATUS_ERROR].append(chapter_id)
                # Recheck R2 artifacts after resync attempt (or initial check if no resync)
                # NOTE: Chapters without moves do NOT require R2 artifacts
                pgn_exists = pgn_v2_repo.exists_pgn(chapter_id) if has_moves else True
                tree_exists = pgn_v2_repo.exists_tree_json(chapter_id) if has_moves else True
                fen_index_exists = pgn_v2_repo.exists_fen_index(chapter_id) if has_moves else True

                if not pgn_exists:
                    report["r2_missing_pgn"].append(chapter_id)
                if not tree_exists:
                    report["r2_missing_tree_json"].append(chapter_id)
                if not fen_index_exists:
                    report["r2_missing_fen_index"].append(chapter_id)
                # Only check metadata for chapters WITH moves (empty chapters have no R2 metadata)
                elif has_moves and (chapter.pgn_hash is None or chapter.pgn_size is None or chapter.r2_etag is None):
                    # If metadata is missing but PGN exists, also resync to populate metadata
                    logger.warning(f"Chapter metadata (hash/size/etag) missing for {chapter_id}. Resyncing...")
                    report["resync_attempts"] += 1
                    try:
                        await pgn_sync_service.sync_chapter_pgn(chapter_id)
                        report["resync_success"] += 1
                        chapter = await study_repo.get_chapter_by_id(chapter_id)
                        if chapter:
                            chapter.pgn_status = PGN_STATUS_READY
                            await study_repo.update_chapter(chapter)
                            report["pgn_status_updates"][PGN_STATUS_READY].append(chapter_id)
                        repaired_chapter = True
                    except Exception as sync_exc:
                        logger.error(f"Failed to resync PGN for chapter {chapter_id} (metadata): {sync_exc}")
                        report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(sync_exc)})
                        report["resync_failures"] += 1
                        chapter.pgn_status = PGN_STATUS_ERROR
                        await study_repo.update_chapter(chapter)
                        report["pgn_status_updates"][PGN_STATUS_ERROR].append(chapter_id)


            except Exception as e:
                logger.error(f"Error checking R2 for chapter {chapter_id}: {e}")
                report["pgn_sync_failures"].append({"chapter_id": chapter_id, "error": str(e)})
            
            if repaired_chapter:
                report["chapters_repaired"] += 1
            else:
                # Chapters that passed all checks (including chapters without moves)
                # should be marked as ready if not already updated
                if chapter_id not in report["pgn_status_updates"][PGN_STATUS_MISMATCH] and \
                   chapter_id not in report["pgn_status_updates"][PGN_STATUS_MISSING] and \
                   chapter_id not in report["pgn_status_updates"][PGN_STATUS_ERROR] and \
                   chapter_id not in report["pgn_status_updates"][PGN_STATUS_READY]:
                    chapter = await study_repo.get_chapter_by_id(chapter_id)
                    if chapter and chapter.pgn_status != PGN_STATUS_READY:
                        chapter.pgn_status = PGN_STATUS_READY
                        await study_repo.update_chapter(chapter)
                        report["pgn_status_updates"][PGN_STATUS_READY].append(chapter_id)
                        logger.info(f"Chapter {chapter_id} marked as ready (passed all checks)")

        await session.commit()
        logger.info("PGN integrity scan completed.")

    # Output report
    _write_report_files(report)
    print(f"Scan report written to: {REPORT_PATH}")
    print(f"Scan summary written to: {SUMMARY_PATH}")
    print(f"Acceptance record written to: {ACCEPTANCE_PATH}")


if __name__ == "__main__":
    asyncio.run(scan_pgn_integrity())
