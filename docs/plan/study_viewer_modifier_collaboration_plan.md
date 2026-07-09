# Study Viewer Modifier Collaboration Plan
Created at: 2026-07-09 00:43 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:43 EDT
Last Modified by: Codex

## inferred requirement
- Source requirement: `docs/requirements/study_viewer_modifier_collaboration.md`
- Todo source: `patch/docs/Jul_8_代办.md`

## implementation plan
1. Add a workspace permission helper that returns effective permission and write capability for a node.
2. Extend study and node responses with `effective_permission` and `can_edit` where study clients need it.
3. Add write-access guards to patch tree save and study chapter mutation endpoints.
4. Add chapter tree revision persistence around tree saves so clients can detect remote updates.
5. Update share UI to choose view/edit access when inviting and changing members.
6. Update study frontend context/page to load `canEdit`, suppress autosave for viewers, and disable mutating controls.
7. Add focused tests for viewer/editor write boundaries.
8. Run targeted tests, frontend build, update the todo document, commit, push, and deploy.

## verification plan
- `ALLOW_CONFIG_WARNINGS=1 DEBUG=false WORKSPACE_TEST_AUTH=1 .venv/bin/python -m pytest ...`
- `python -m py_compile patch/backend/study/api.py backend/modules/workspace/api/endpoints/studies.py`
- `npm run build` in `frontend/web`
- Production smoke after deployment for study read and API health.
