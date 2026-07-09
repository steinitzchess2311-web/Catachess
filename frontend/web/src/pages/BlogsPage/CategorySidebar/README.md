## header
Created at: 2026-07-09 01:18 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:42 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Provide blog navigation, category switching, and authoring entry points for the blog page.
- 架构思路: Keep the sidebar shell in `CategorySidebar.tsx` and isolate official categories, user actions, and collapse controls in small components.

## folder structure
|-CategorySidebar.tsx sidebar shell and responsive collapsed state
|-CollapsedView.tsx rail navigation when the sidebar is collapsed
|-CommunityButton.tsx community article navigation
|-OfficialSection.tsx official category navigation
|-PinnedButton.tsx pinned article navigation
|-ToggleButton.tsx collapse and expand control
|-UserActionsSection.tsx create, draft, and article management shortcuts

## 代办
- Connect draft/article management shortcuts to dedicated product screens when those routes exist.
