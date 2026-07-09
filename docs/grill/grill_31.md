## header
Created at: 2026-07-09 02:06 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:06 EDT
Last Modified by: Codex

## topic
Large PGN import loading modal spacing and product polish.

## grill
- What is actually broken? The parsing progress card is visually trapped between the modal header and footer, with too little vertical breathing room and weak hierarchy.
- What should stay unchanged? Worker parsing, import batching, cancellation, and progress math should remain untouched.
- Where should the fix live? The `LargePgnImportModal` should get scoped body/footer classes, with CSS in the shared patch style file because modal primitives already live there.
- What makes it product-level? The modal needs a clear header, padded content body, calm progress panel, legible count line, and a footer that feels intentionally separated instead of accidental.

## decision
- Add a dedicated large PGN modal body and footer layout.
- Increase progress card padding and vertical rhythm only inside the large PGN modal.
- Remove inline spacing from parsing/importing progress states.
