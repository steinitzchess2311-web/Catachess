# Profile Title Header Cleanup Requirements
Created at: 2026-07-08 21:07 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:07 EDT
Last Modified by: Codex

## brief intro
- goal: Simplify the profile hero and edit profile form so identity, titles, ratings, and logout controls are not duplicated.
- 架构思路: Keep existing profile fields and API shape, but constrain the Chinese title UI and public title rendering rules.

## requirements
- Public profile hero must not show rating cards.
- Public profile hero must not show FIDE or Chinese titles as separate pills.
- Public profile hero name must render as `{FIDE title} {username}` when a FIDE title exists.
- If no FIDE title exists, public profile hero name must render as `{Chinese title} {username}` when a Chinese Chess Association title exists.
- If both titles exist, only the FIDE title may be used in the hero display.
- Chinese Chess Association Title must be selected from `三运`, `二运`, `一运`, `候补`, `棋协`.
- Existing legacy Chinese title labels such as `国家三级运动员` must display as the short equivalent where possible.
- The edit profile page must remove the helper sentence under `About You`.
- The edit profile page must remove logout from the edit header.
- The edit profile page must remove the sentence `Your public profile is visible to everyone on Catachess.`

## folder structure
|-profile_title_header_cleanup.md requirements for the profile hero/title cleanup

## 代办
- Decide later whether to rename the persisted `chinese_athlete_title` field to a Chinese Chess Association specific field.
