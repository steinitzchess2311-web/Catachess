# Share Visibility Description Removal Requirements

## header
Created at: 2026-07-08 20:58 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:58 EDT
Last Modified by: Codex

## brief intro
- goal: Remove secondary explanatory text from workspace share visibility cards.
- 架构思路: Keep visibility choice behavior unchanged while reducing visual noise in the modal.

## folder structure
|-share_visibility_description_removal.md requirements for share visibility card copy cleanup

## Requirements
- The visibility cards must show only icon and label.
- The strings `Anyone can view`, `Only you`, and `Specific people` must not render in the share modal.
- Public, Private, and Shared selection behavior must remain unchanged.
- The shared-users panel must remain unchanged.
- Card spacing must be tightened after removing the secondary text.

## Non-Requirements
- Do not change backend visibility semantics.
- Do not remove cascade warnings for folder visibility changes.

## 代办
- None.
