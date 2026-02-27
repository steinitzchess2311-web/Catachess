# Classroom Button Logic

This document defines the button hierarchy and interaction logic for classroom detail pages.
Goal: remove parallel actions, establish clear priority, and reduce user confusion.

## Core Principle

Use action hierarchy, not action equality.
At any moment, the page must communicate:
1. What is the primary action now.
2. What are optional secondary actions.
3. What is dangerous/rare and should be hidden behind a menu.

## Action Levels

### Level 1: Primary Action (exactly 1)

- One filled blue button only.
- Represents the most likely next step for current role/state.
- Must appear in the main header action area.
- Never duplicate this action elsewhere on the same screen.

### Level 2: Secondary Actions (max 2)

- Outline/ghost style.
- Useful but non-critical actions.
- May appear next to primary action.
- If more than 2 exist, keep top 2 and move rest to `More`.

### Level 3: Utility / Destructive / Rare Actions

- Hidden under a `More` menu (kebab or settings).
- Includes settings, archive, dissolve class, leave class, folder utilities.
- Destructive actions must not be exposed as first-line buttons.

## Placement Rules

### Header Zone

- Only global/classroom-level actions.
- Max visible buttons: 3 total (1 primary + up to 2 secondary).
- No tab-specific duplicates in header.

### Overview Body Zone

- Only contextual section actions.
- Each section can have at most 1 visible action.
- Additional section actions go into local section menu.

### Tab Pages

- Actions should be local to tab context.
- Do not repeat Overview CTA in Assignments/Members unless state truly differs.

## No-Duplication Rule

Never show the same semantic action in two places on the same page.
Examples to avoid:
- `Announce` in header and `Broadcast Announcement` in overview action row.
- Multiple chat-entry buttons in header + body.

If an action must be globally available, keep it in header and remove body duplicate.

## Role-Based Priority

## Teacher / Owner

### Primary (choose one by state)

- Default: `Create Assignment`
- If urgent comms needed (e.g., no recent announcement and pending due tasks spike): `Announce`

Do not show both as primary at the same time.

### Secondary (max 2)

- `Announce` (when primary is Create Assignment)
- `Open Class Chat`

### More Menu

- `Student Folders`
- `Rename Classroom`
- `Archive / Unarchive`
- `Dissolve Class` (owner only, destructive)
- `Class Settings`

## Student

### Primary

- `Continue Tasks` (jump to actionable todo/assignment list)

### Secondary (max 2)

- `Open Class Chat`
- `Share to Teacher` (if workspace sharing is enabled)

### More Menu

- `Leave Class`
- Any low-frequency utilities

## State-Based Adaptation

Buttons should adapt to state, not remain static.

- If no assignments exist for teacher: keep `Create Assignment` primary.
- If there are overdue submissions and recent announcements are stale: switch primary to `Announce` temporarily.
- If student has zero pending tasks: keep `Continue Tasks` as primary but label can soften to `View Assignments`.

## Visual Hierarchy Rules (Blue-White Theme)

- Only one high-emphasis button per screen.
- Secondary actions use low-contrast outlines.
- More menu trigger should be visually quiet.
- Do not encode priority by many colors; encode by contrast and placement.

## Density Guardrails

- Same row: max 3 visible actions.
- Same section header: max 1 explicit action.
- If action count exceeds limits, collapse extras into `More`.

## Accessibility and Clarity

- Use explicit verbs: `Create Assignment`, `Open Class Chat`, `Leave Class`.
- Avoid ambiguous labels like `Open`, `Go`, `Action`.
- Ensure keyboard focus order follows visual priority.
- Keep destructive actions separated with divider + danger color in menu.

## Implementation Checklist

1. Inventory all buttons in classroom detail + tabs.
2. Assign each button a level (L1/L2/L3).
3. Remove duplicates (same semantic action).
4. Enforce per-zone max button counts.
5. Apply role and state gating.
6. Validate with empty, active, and high-activity classrooms.

## Current Immediate Fix Plan

1. Keep one primary CTA in header.
2. Keep at most two secondary actions in header.
3. Move settings/archive/dissolve/leave/folders to `More`.
4. Remove duplicate announce/chat actions from overview body.
5. Keep section-level action limit to one visible trigger.
