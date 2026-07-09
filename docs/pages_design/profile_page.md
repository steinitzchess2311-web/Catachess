# Profile Page Design
Created at: 2026-07-08 21:07 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal: Document the public profile and edit profile product layout.
- 架构思路: Public profile separates identity from details; edit profile keeps controls compact and avoids explanatory copy where labels are clear.

## public profile layout
- Hero: avatar, one identity line, and owner actions.
- Identity line: show `FIDE title + username` when a FIDE title exists; otherwise show `Chinese Chess Association title + username` when present; otherwise show username only.
- The title prefix in the identity line uses the orange accent; the username remains dark primary text.
- Ratings are not shown in the hero. Ratings belong in the detail card so they appear once.
- Total online time is a detail card sourced from stored profile statistics, not recalculated on page load.
- Logout may appear on the owner public profile actions, not in edit profile.
- Logout confirmation uses a centered modal with dim backdrop, explicit cancel/log out actions, outside click dismissal, and Escape dismissal.

## edit profile layout
- Sticky header contains back, title, and save.
- No profile visibility explainer appears below the edit page title.
- Chess Identity contains FIDE title choices, `中国棋协称号 (Chinese Chess Association Title)` choices, and rating inputs.
- Chinese Chess Association Title choices are `三运`, `二运`, `一运`, `候补`, `棋协`.
- About You is a plain textarea without helper subcopy.

## folder structure
|-profile_page.md design notes for public profile and edit profile pages

## 代办
- Replace legacy `Chinese Athlete Title` naming in backend schema when a migration window is available.
