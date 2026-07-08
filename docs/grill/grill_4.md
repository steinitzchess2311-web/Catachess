## header
Created at: 2026-07-08 13:45:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 13:45:00 EDT
Lst Modified by: Codex

## topic auth session lifetime and unexpected logout

1. What is the deployed token lifetime?
The running `catachess-railway-api.service` process has `ACCESS_TOKEN_EXPIRE_MINUTES=60`, so production tokens expire after 60 minutes.

2. Is the repository default aligned with production?
No. `backend/core/config.py` had an extremely large default value. That is risky because `datetime + timedelta(minutes=...)` can overflow if the default is used.

3. Why can the UI look like it logged out unexpectedly?
The shared browser API client cleared `catachess_token` and `catachess_user_id` on every HTTP 401 response. Optional background calls such as chat notifications or current-game polling can therefore clear the whole session even when the main page is otherwise usable.

4. What should be changed first?
Use a bounded 30-day access token lifetime and clear stored auth only when the current-user identity probe fails.

5. What is the post-fix production value?
The server-local `.env.production` was changed to `ACCESS_TOKEN_EXPIRE_MINUTES="43200"` and the API service was restarted.
