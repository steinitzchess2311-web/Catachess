# Node Actions Duplicate Modified Date Grill

## header
Created at: 2026-07-08 20:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:05 EDT
Last Modified by: Codex

## topic node actions duplicate modified date

### 1. What is duplicated?
The node action modal header shows `Modified MM/DD/YYYY`, while the body metadata already shows `Updated MM/DD/YYYY`.

Recommended answer: remove the header `Modified` line and keep the body metadata as the single timestamp surface.

### 2. Should all timestamps be removed?
No. The user called out the header line as redundant, not the metadata block.

Recommended answer: preserve `Created` and `Updated` in the body because they are grouped as details and do not compete with the title.

### 3. Is this an architectural decision?
No. This is a reversible product polish change with no backend or data model impact.

Recommended answer: skip ADR creation and record the rule in workspace page design docs.
