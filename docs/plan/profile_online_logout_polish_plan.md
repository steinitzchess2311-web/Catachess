# Profile Online Time And Logout Polish Plan
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal: Implement `docs/requirements/profile_online_logout_polish.md`.
- 架构思路: Add one read-only profile statistic field, normalize it through the frontend API layer, then apply minimal product UI changes.

## plan
- Add `total_online_seconds` to backend profile response models and response builders.
- Add `total_online_seconds` to frontend profile types and API normalization fallbacks.
- Render a total online time card in `PublicProfilePage`.
- Split the hero title prefix into an orange inline span.
- Rename the edit profile Chinese title label.
- Redesign `LogoutButton` as a centered confirmation modal with outside click and Escape handling.
- Update profile page design documentation.
- Mark the four completed profile todo lines after build and backend checks pass.

## folder structure
|-profile_online_logout_polish_plan.md implementation plan for profile online time and logout polish

## 代办
- Verify the deployed public profile response includes `total_online_seconds`.
