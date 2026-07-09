# Profile Title Header Cleanup Plan
Created at: 2026-07-08 21:07 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:07 EDT
Last Modified by: Codex

## brief intro
- goal: Implement `docs/requirements/profile_title_header_cleanup.md`.
- 架构思路: Make the frontend display rules deterministic first, then add a narrow backend guard so future writes stay in the approved option set.

## plan
- Add shared frontend constants for Chinese Chess Association title choices and legacy normalization.
- Remove hero rating cards and separate title badges from `PublicProfilePage`.
- Render the hero identity as a single username line with an optional title prefix.
- Convert the edit form Chinese title field from free text to a button group.
- Remove edit profile subtitle, edit logout button, and `About You` helper copy.
- Add backend normalization/validation for the existing `chinese_athlete_title` field.
- Update profile page design docs.
- Run frontend build and targeted backend syntax checks.
- Verify the public page visually with a screenshot when possible.

## folder structure
|-profile_title_header_cleanup_plan.md implementation plan for profile title/header cleanup

## 代办
- Add route-level backend tests once the profile router test fixture is available.
