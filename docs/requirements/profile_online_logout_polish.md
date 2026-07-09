# Profile Online Time And Logout Polish Requirements
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal: Finish the remaining Jul 8 profile polish items around title color, online time, Chinese title label, and logout confirmation.
- 架构思路: Reuse existing profile/statistics storage and keep UI changes within the profile and logout components.

## requirements
- The profile title prefix before the username must render in orange.
- Public and private profile responses must include stored `total_online_seconds`.
- Public profile must display total online time in a compact detail card.
- Missing or zero online time must display a stable empty state rather than hiding the card.
- Edit profile must label the Chinese title section as `中国棋协称号 (Chinese Chess Association Title)`.
- The profile logout confirmation must use a product-level centered modal with backdrop dismissal and keyboard Escape dismissal.
- Logout must still clear local/session auth tokens and redirect to `/login` even if the backend logout call fails.

## folder structure
|-profile_online_logout_polish.md requirements for remaining profile polish items

## 代办
- Add automated profile router tests after auth fixtures are available.
