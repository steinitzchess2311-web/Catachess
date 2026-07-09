# Study Permissions Collaboration Grill
Created at: 2026-07-09 00:43 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:43 EDT
Last Modified by: Codex

## topic study viewer modifier collaboration

### 1. Should the database add a new `modifier` permission?

Recommended answer: No. The workspace ACL model already has `viewer`, `commenter`, `editor`, `admin`, and `owner`, and `editor` is the existing write-capable role. Adding `modifier` would duplicate meaning and split permission checks. The product label can say "Can edit" or "Modifier", while the database stores `editor`.

### 2. What is the strict permission boundary?

Recommended answer: A viewer can open the study, chapters, tree, explorer, and exports. Only owner/admin/editor can save tree JSON, create/update/delete/reorder/import chapters, or use legacy variation mutation endpoints.

### 3. How should the frontend avoid misleading viewers?

Recommended answer: Fetch the current user's effective permission with the study payload, expose `canEdit`, disable mutating controls in the study shell, and make autosave no-op for read-only users. The backend still remains authoritative.

### 4. What is the smallest safe multi-editor update model?

Recommended answer: Keep the existing whole-tree JSON save contract, but add monotonically increasing chapter tree revisions and conflict-aware saves. When two editors save the same chapter, the server records a revision event; clients can poll for revision changes and reload/notify without needing every user synchronized into one live cursor/page session.

### 5. What must be tested first?

Recommended answer: Server-side behavior. A shared viewer must get HTTP 403 when saving a tree; a shared editor must be able to save. UI checks are product polish, not security.

### 6. What is out of scope for this pass?

Recommended answer: Full operational transform, per-move CRDT, shared cursor presence, and simultaneous same-node merge UI. Those require a different tree storage model and should not block safe viewer/editor collaboration.
