Stage 03 - Tree Init Consistency

Goal
- Ensure tree.json exists and matches patch schema when entering study.

Must-reference paths
- patch/backend/study/api.py
- patch/tree/StudyTree.ts
- patch/tree/type.ts

Constraints
- No FEN persistence.
- Use TREE_SCHEMA_VERSION.

Checklist
- [ ] Initialize empty tree.json using createEmptyTree() shape.
- [ ] Verify tree.json version matches TREE_SCHEMA_VERSION; upgrade if missing version.
- [ ] Do not attempt to load legacy PGN for patch flow.
- [ ] Log tree init and load failures for debugging.
- [ ] Write completion report in patch/docs/chapter_fix/summary/ChapterFix_stage03.md.
