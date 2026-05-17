# Frontend Web

React + Vite web client for Catachess.

## Responsibilities

- Mount public pages, auth pages, workspace routes, patch study editor routes, live-game routes, classrooms, blogs, and profile pages.
- Hold browser auth state and pass stable user identity into feature modules.
- Produce the production build consumed by deployment.

## Important Files

- `src/App.tsx`: top-level routing, auth gate, `UserContext` provider, lazy feature mounts.
- `src/contexts/UserContext.tsx`: shared user profile shape.
- `src/components/header/Header.tsx`: global navigation, notifications, current-game polling.
- `src/components/dialogBox/CreateModal.tsx`: workspace create flow for folders and studies.

## Identity Rules

- `username` is the public/game-facing user name returned by `/user/profile`.
- `userId` is the JWT subject UUID and is stored under `catachess_user_id`.
- Do not use JWT `sub` as a temporary `username`. Live games use the supplied player id as identity; changing from username to UUID breaks current-game lookup and WebSocket reconnect.
- While profile loading fails or is pending, keep `username` as `null` rather than falling back to UUID.

## Build

```bash
npm run build
```

Known build warnings about large chunks and mixed dynamic/static imports are pre-existing bundle-shaping warnings, not fatal build errors.
