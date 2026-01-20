Stage 01 - Enter Study: Chapter Resolution

Goal
- Guarantee a chapterId exists before patch loads tree.json.

Must-reference paths
- Frontend entry: frontend/web/src/App.tsx (patch route)
- Patch state: patch/studyContext.tsx
- Patch API: patch/backend/study/api.py
- Legacy study API (chapter list/create)

Constraints
- No new DB fields.
- Chapter IDs must come from legacy backend.
- R2 keys must remain chapters/{chapter_id}.tree.json.

Checklist
- [ ] On study entry, call legacy API to list chapters for the study.
- [ ] If list is empty, call legacy API to create a default chapter.
- [ ] Use the returned chapterId to set patch state (SET_CHAPTER).
- [ ] After chapterId is set, call patch GET /study-patch/chapter/{chapter_id}/tree.
- [ ] If tree.json missing, call patch PUT with empty tree to initialize.
- [ ] If any step fails, surface LOAD_ERROR and stop entry.
- [ ] Document default chapter title/order and startFen rules.
- [ ] Write completion report in patch/docs/chapter_fix/summary/ChapterFix_stage01.md.
