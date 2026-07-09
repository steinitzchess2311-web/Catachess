## header
Created at: 2026-07-08 21:07 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:07 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Own the public profile and edit profile frontend module.
- 架构思路: Keep API normalization, profile types, public profile display, edit form behavior, and module styles colocated so profile title/rating display rules are easy to audit.

## folder structure
|-api.ts profile API client and response normalization
|-EditProfilePage.tsx authenticated edit profile page
|-index.ts module exports
|-PublicProfilePage.tsx public profile page
|-types.ts profile data types and title option constants
|-user_profile.css profile module styling

## 代办
- Rename `chinese_athlete_title` to a Chinese Chess Association specific API field during a future migration window.
