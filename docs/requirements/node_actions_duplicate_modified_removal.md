# Node Actions Duplicate Modified Removal Requirements

## header
Created at: 2026-07-08 20:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:05 EDT
Last Modified by: Codex

## brief intro
- goal: Remove duplicate modified-date copy from the workspace node action modal header.
- 架构思路: Keep the modal hierarchy focused on object type and title, with timestamps consolidated in the metadata block.

## folder structure
|-node_actions_duplicate_modified_removal.md requirements for removing duplicate modified text

## Requirements
- The workspace node action modal header must not show `Modified MM/DD/YYYY`.
- The node action modal body must continue to show `Created` and `Updated` metadata.
- The modal close, share, move, rename, and recycle actions must remain unchanged.
- No backend API or data model change is required.

## 代办
- Apply the same no-duplicate-header-metadata rule if new workspace action modals are added.
