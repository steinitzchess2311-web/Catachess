## header
Created at: 2026-07-08 19:12:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 19:12:00 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Shared utility functions for blog article metadata that do not belong in route handlers or storage services.
- 架构思路: Keep deterministic parsing and relation sync helpers here, while R2 upload stays in services and HTTP validation stays in api.

## folder structure
|-__init__.py package marker for blog utilities
|-image_linker.py extracts article image URLs and syncs image/article database relationships

## 代办
- Add focused tests for image URL extraction and article-image relation sync.
