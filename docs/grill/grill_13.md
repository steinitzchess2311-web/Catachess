# Workspace And Study Modal Product Redesign Grill

## header
Created at: 2026-07-08 20:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:05 EDT
Last Modified by: Codex

## topic workspace and study modal redesign

### 1. What is the real user-facing problem?
The workspace and study workflows have several modal styles that look unrelated: emoji headers, oversized centered titles, inconsistent button hierarchy, and high-radius cards. This makes the product feel less mature even when the underlying actions are correct.

Recommended answer: keep the current functional surface but replace modal chrome with one quiet, blue-white product language.

### 2. Should this rewrite every page at once?
No. A full app-wide rewrite risks regressions across unrelated modules. The safest product-level step is to update the shared workspace node dialogs and the analysis-to-study picker because those are the visible modal surfaces in the workspace/study flow.

Recommended answer: scope this pass to workspace node actions, create/rename/move/delete/share dialogs, drag-move confirmation, trash actions, and the analysis study picker.

### 3. What visual rules should guide the redesign?
Use white surfaces, slate text, blue primary actions, compact spacing, 8-10px radius, and restrained shadows. Icons clarify actions, but emoji should not carry the visual system.

Recommended answer: remove emoji-driven UI, reduce rounded cards, use consistent header/body/footer sections, and make destructive actions explicit but not theatrical.

### 4. What functionality must remain?
All existing create, rename, move, delete, restore, purge, share visibility, user search, add/remove share user, and send-analysis-to-study behavior must stay intact.

Recommended answer: change markup and CSS only where needed for product quality; preserve existing API calls and retry behavior.

### 5. What is the likely risk?
Dialog components are mounted from the legacy workspace module into React roots, and the analysis picker lives separately. Styling names must not collide with the broader app.

Recommended answer: use a small shared dialog CSS file with `cc-dialog-*` utility classes plus component-specific classes for advanced panels.
