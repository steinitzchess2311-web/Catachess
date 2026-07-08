# Email And Workspace Product Redesign Plan
Created at: 2026-07-08 13:08:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 13:08:00 EDT
Last Modified by: Codex

## brief intro
- goal: Execute `docs/requirements/email_workspace_product_redesign.md`.
- 架构思路: Inspect current UI first, then make scoped template/CSS changes and validate with build plus screenshots.

## plan
1. Read current email templates, workspace templates/styles, and study reference styles.
2. Run the frontend against the production API and capture current workspace screenshots.
3. Redesign `signup_code.html` and `signup_code.txt` with blue-white logo branding.
4. Redesign workspace template/CSS and only adjust rendering markup where CSS hooks need stable structure.
5. Run frontend build and backend template sanity checks.
6. Capture updated workspace screenshots at desktop and mobile widths.
7. Sync changed backend/frontend files to the server and restart only affected services.

## folder structure
|-email_workspace_product_redesign_plan.md execution plan for email and workspace redesign

## 代办
- Decide whether to make workspace a full React page in a later refactor.
