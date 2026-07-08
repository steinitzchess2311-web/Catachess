# Email And Workspace Product Redesign Requirements
Created at: 2026-07-08 13:08:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 13:08:00 EDT
Last Modified by: Codex

## brief intro
- goal: Redesign the signup verification email and workspace browser to a product-grade blue-white CataChess experience.
- 架构思路: Keep backend email behavior and workspace data/actions stable, while improving presentation through templates, CSS, and minimal DOM structure changes.

## requirements
- Signup verification email must use CataChess logo branding and a blue-white palette.
- Signup verification email must avoid decorative gradients and noisy colors.
- Signup verification email must remain compatible with common email clients by using table/inline-friendly styles.
- Workspace redesign must preserve the majority of current functions: navigation modes, search, sorting, path jump, creation, open, rename, move, delete, share, trash actions, and guest gating.
- Workspace redesign must be checked with screenshots before and after implementation.
- Workspace layout should feel like a work-focused product surface, closer to the study page's panel clarity and density.
- Text and controls must not overlap on desktop or mobile.

## folder structure
|-email_workspace_product_redesign.md requirements for email and workspace product redesign

## 代办
- Add automated visual regression once the frontend has a committed screenshot test harness.
