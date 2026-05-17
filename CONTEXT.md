# Product Context

## Glossary

### Study

A user-owned chess workspace item that contains one or more chapters. In storage, a Study is a `nodes` row with `node_type=study` plus a matching `studies` row.

### Chapter

One playable/analyzable game tree inside a Study. Chapter metadata lives in SQL; the move tree lives in R2 as `tree.json`.

### Default Chapter

The initial `Chapter 1` created for a new Study. It must exist for studies created through both `/studies` and `/nodes`.

### Username

The public user name returned by `/user/profile`. It is used by live-game UI as the authenticated player identity.

### User ID

The JWT subject UUID stored in browser auth state as `catachess_user_id`. It is not a fallback display name and must not replace Username in live-game flows.
