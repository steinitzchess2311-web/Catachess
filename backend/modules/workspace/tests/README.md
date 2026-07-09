## header
Created at: 2026-07-09 01:04 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:42 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Provide focused unit and API tests for the workspace backend.
- 架构思路: Tests use in-memory SQLite and FastAPI ASGI clients where possible, with fake storage clients for R2 boundaries.

## folder structure
|-conftest.py shared async database, repository, service, and auth fixtures.
|-test_api_nodes.py node API behavior tests.
|-test_share_service.py ACL/share service tests.
|-test_share_notifications.py share invitation notification regression tests.
|-test_study_permissions_collaboration.py study viewer/editor write-boundary tests.
|-test_api_variation_endpoints.py legacy variation endpoint tests.

## 代办
- Keep security boundary tests close to API routes so authorization regressions fail before deployment.
