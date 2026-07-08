## header
Created at: 2026-07-08 13:45:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 13:45:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Implementation plan for fixing short auto logout behavior.
- 架构思路: Change the minimal backend configuration and frontend auth-clearing behavior, then verify build and deployment.

## related requirement
- docs/requirements/auth_session_lifetime.md

## plan
1. Confirm the deployed token lifetime from the running process environment.
2. Replace the unsafe huge backend default with a bounded 30-day value.
3. Update the shared frontend API client so only `/user/profile` 401 clears stored auth.
4. Update the server-local production environment to the same 30-day value.
5. Build the frontend and restart only the CataChess Railway API service.

## result
- Server `.env.production` now uses `ACCESS_TOKEN_EXPIRE_MINUTES="43200"`.
- `catachess-railway-api.service` was restarted and verified healthy.

## 代办
- Add a dedicated API-client unit test when frontend test scaffolding for shared UI assets is introduced.
