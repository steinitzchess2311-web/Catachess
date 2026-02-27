# Classroom Button Mapping

This file maps current classroom-detail actions to the new hierarchy defined in `buttons.md`.

## Scope

- In scope: classroom detail header + overview actions for teacher/student.
- Out of scope: modal internal confirm/cancel buttons (kept local to modal behavior).

## Legend

- `L1`: Primary (only one visible filled button)
- `L2`: Secondary (max two visible)
- `L3`: Utility/destructive/rare (move to `More`)

## Teacher / Owner Mapping

| Current location | Current label | Current issue | New level | New location | Rule |
|---|---|---|---|---|---|
| Header | `Announce` | Duplicates body-level broadcast action | L2 (default) / L1 (state switch) | Header action row | Keep visible, but never duplicate in body |
| Header | `Leave Class` (non-owner only) | Danger action too exposed in top row | L3 | `More` menu | Keep destructive/exit actions in menu |
| Header settings dropdown | `Rename` | Utility action buried correctly but mixed with destructive without grouping | L3 | `More > Class settings` group | Keep as utility menu item |
| Header settings dropdown | `Archive` / `Unarchive` | Potentially destructive but same visual weight as utility | L3 | `More` with divider above destructive section | Separate by divider + danger style |
| Header settings dropdown | `Dissolve Class` | Destructive action | L3 | `More` danger section | Never first-line |
| Overview action row | `Broadcast Announcement` | Semantic duplicate of `Announce` | Remove | N/A | Delete from overview |
| Overview action row | `Open Class Chat` | Competes with announce as same-level utility | L2 | Header action row (if selected in top-2) | Keep max two secondary actions |
| Overview action row | `Student Folders` | Utility action too prominent | L3 | `More` menu | Move out of primary scanning path |

## Student Mapping

| Current location | Current label | Current issue | New level | New location | Rule |
|---|---|---|---|---|---|
| Header | (none today) | No explicit primary CTA for student | L1 | Header action row | Add `Continue Tasks` |
| Overview action row | `Open Class Chat` | Good action but currently competes with peer actions | L2 | Header action row | Keep visible as secondary |
| Overview action row | `Share to Teacher` | Useful but should not compete with primary task completion | L2 (conditional) | Header secondary or Tasks section header | Show only when sharing is enabled |
| Header / menu | `Leave Class` | Exit action should not be peer with productive actions | L3 | `More` menu | Keep separated from productive actions |

## Global Structural Changes

1. Keep max `3` visible actions in header (`1x L1 + up to 2x L2`).
2. Remove overview-level duplicate actions already present in header.
3. Keep section headers to max `1` visible action each.
4. Route all destructive/rare actions into `More`.

## Suggested Final Visible Actions by Role

### Teacher / Owner (default state)

- `L1`: `Create Assignment`
- `L2`: `Announce`
- `L2`: `Open Class Chat`
- `L3` in `More`: `Student Folders`, `Rename Classroom`, `Archive/Unarchive`, `Dissolve Class`, `Class Settings`

### Teacher / Owner (urgent comms state)

- `L1`: `Announce`
- `L2`: `Create Assignment`
- `L2`: `Open Class Chat`
- `L3` unchanged in `More`

### Student

- `L1`: `Continue Tasks`
- `L2`: `Open Class Chat`
- `L2`: `Share to Teacher` (conditional)
- `L3` in `More`: `Leave Class`, low-frequency utilities

## Acceptance Checks

1. No duplicated semantic action appears in both header and overview.
2. Exactly one filled high-emphasis button is visible per role/state.
3. No destructive action appears outside `More`.
4. Teacher and student both have an explicit primary CTA.
5. Header action count never exceeds three visible buttons.
