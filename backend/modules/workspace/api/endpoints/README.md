# Workspace API Endpoints

REST handlers for the workspace module.

## Responsibilities

- Parse HTTP requests and return Pydantic response models.
- Delegate business rules to domain services.
- Translate domain errors into HTTP status codes.

## Important Files

- `nodes.py`: tree node CRUD. Study node creation must call the default chapter service.
- `studies.py`: study/chapter/move APIs. Direct study creation also calls the default chapter service.
- `discussions*.py`: discussion thread and reply APIs.
- `notifications.py`, `presence.py`, `versions.py`, `search.py`, `users.py`: supporting workspace features.

## Endpoint Rule

Do not duplicate study bootstrap logic in endpoint handlers. If a handler creates a study, it must go through the shared domain service that creates or verifies `Chapter 1`.
