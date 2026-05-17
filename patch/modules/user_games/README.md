# User Games Frontend Module

Live-game frontend slice for creating, joining, reconnecting to, and playing games through `https://gameserver.catachess.com`.

## Responsibilities

- `/play`: create challenges/open games.
- `/chess/:gameId/join`: join shared open games.
- `/chess/:gameId`: connect to the live game WebSocket and play.
- `/chess/:gameId/analyze`: view completed game analysis.

## Important Files

- `api.ts`: HTTP and WebSocket URL helpers.
- `PlayPage.tsx`: lobby entry.
- `JoinGamePage.tsx`: open-game join flow.
- `LiveGamePage.tsx`: live board, clocks, controls, reconnect.
- `hooks/useGuestId.ts`: guest and anonymous per-game IDs.
- `hooks/useGameWs.ts`: WebSocket state machine.

## Identity Contract

- The game server treats `user_id` as the player identity string.
- Authenticated play should use the stable public username supplied by `App.tsx`.
- Guest play uses `guest_*`.
- Anonymous join links may return `anon_user_id`; store it per game and use it for later WebSocket reconnect.
- Never silently replace a username with the JWT UUID. That creates a different game identity and makes current-game lookup, abort, and reconnect fail.
