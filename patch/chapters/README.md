## header
Created at: 2026-07-09 01:20 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:20 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder.
- Study chapter list, creation modal, and chapter loading hooks for the patch study page.
- 架构思路
- Keep chapter CRUD and tree bootstrapping in a dedicated hook so the page shell only coordinates layout and access state.

## folder structure
|-NewChapterModal.tsx modal for creating one or more chapters
|-useChapters.ts hook for chapter CRUD, ordering, and tree loading

## 代办
- Keep all write paths gated by the study access capability returned from the backend.
