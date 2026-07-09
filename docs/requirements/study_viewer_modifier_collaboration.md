# Study Viewer Modifier Collaboration Requirements
Created at: 2026-07-09 00:43 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:43 EDT
Last Modified by: Codex

## brief intro
- goal for this requirement: Make shared studies distinguish read-only viewers from write-capable modifiers and allow multiple modifiers to update study content without silent permission leaks.
- 架构思路: Reuse the existing ACL hierarchy. Treat product "modifier" as the existing `editor` permission, enforce write access at every study mutation boundary, and add a lightweight chapter tree revision signal for multi-editor refresh.

## requirements
- Study sharing must let the owner/admin choose whether an invited user can view only or edit.
- The database permission value for edit-capable users must be `editor`; no duplicate `modifier` enum is introduced.
- Study payloads must expose the current user's effective permission and `can_edit` capability.
- Viewer users may read study metadata, chapters, tree JSON, PGN export, and non-mutating views.
- Viewer users must not save chapter tree JSON.
- Viewer users must not create, update, reorder, delete, or import chapters into an existing study.
- Viewer users must not use legacy move, variation, annotation, or promotion mutation endpoints.
- Editor/admin/owner users must keep existing edit capability.
- The frontend must prevent read-only users from autosaving and from seeing active mutating controls as available.
- Tree saves must carry a monotonic revision so multiple modifiers can detect that another editor updated the chapter.
- If another modifier updates a chapter while the current editor is idle, the client must refresh or show a clear reload path without requiring all users to be on the same synchronized page.
- The implementation must preserve current tree JSON shape and existing study URLs.

## acceptance
- Backend tests prove viewer tree save is rejected and editor tree save is accepted.
- Backend tests or focused checks prove chapter mutation endpoints require edit permission.
- Share UI can add users as view-only or editor and can change an existing shared user's role.
- Study UI derives read-only state from backend effective permission and does not autosave for viewers.
- Frontend build passes.
- Changed backend code compiles or targeted backend tests pass.
