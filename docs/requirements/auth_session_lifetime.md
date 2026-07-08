## header
Created at: 2026-07-08 13:45:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 13:45:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define the expected login-session behavior for CataChess.
- 架构思路: Keep token lifetime controlled by backend configuration, while making the frontend distinguish true authentication failure from optional endpoint failures.

## requirements
- Production login sessions should not expire after only a short active browsing period.
- Access-token lifetime must use a bounded value that Python `datetime` can safely encode.
- A failed current-user identity check should clear stored auth and let protected routes redirect to login.
- A 401 from optional/background API requests must not clear the whole browser session by itself.
- Manual logout must keep clearing local and session storage immediately.

## 代办
- Consider refresh-token support if the product later needs long-lived sessions with short-lived access tokens.
