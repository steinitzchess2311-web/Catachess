# Issue Report: Catachess Backend

**Date:** 2026-01-18
**Author:** Gemini

This document outlines two critical issues identified in the backend system.

---

## 1. Issue: Incorrect Status for Empty PGN Chapters

**Severity:** High
**Status:** Open

### Description

The PGN synchronization logic incorrectly handles chapters that contain no moves (i.e., an "empty tree"). When `pgn_sync_service` encounters such a chapter, it returns `None`. This causes the `pgn_status` field in the database for that chapter to remain `null`, instead of being updated to a final state. As a result, a large number of chapters may never be marked as processed, leading to data inconsistency and potential reprocessing loops.

This issue is present in both the current and legacy code paths.

### Locations

- `backend/modules/workspace/domain/services/pgn_sync_service.py`, line 82
- `backend/modules/workspace/domain/services/pgn_sync_service.py`, line 166

### Suggested Solution

Modify the logic in `pgn_sync_service.py`. Instead of returning `None` for empty chapters, the service should return the status `ready`. This will ensure that all chapters, including those without moves, are correctly marked as processed.

---

## 2. Issue: Missing Migration Enforcement and Documentation

**Severity:** Low
**Status:** Open

### Description

A migration script to add the `pgn_status` column to the database has been created. However, there is no accompanying documentation, acceptance record, or automated check to ensure this migration is executed in production environments before the application code that relies on it is deployed.

If the application is deployed without running the migration (`alembic upgrade head`), any attempt to write to the `pgn_status` column will result in a runtime error, likely causing service disruptions.

### Location

- `backend/modules/workspace/db/migrations/versions/20260118_0017_add_pgn_status.py`

### Suggested Solution

1.  **Acceptance Record:** Create a `migration_acceptance_record.md` to formally document that this migration is a required step for the deployment. This record should be reviewed and signed off by the engineering and QA leads.
2.  **Deployment Checklist:** Add a mandatory step to the production deployment checklist: "Verify `alembic upgrade head` has been executed."
3.  **Startup Check (Optional):** Implement a check on application startup that verifies the presence of the `pgn_status` column in the database and fails to start if it is missing, preventing the application from running in an inconsistent state.
