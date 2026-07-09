Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:20:00 EDT
Last Modified by: Codex

# Classroom Page Design

## Product Intent
Classroom is an operational teaching workspace. It should feel like the workspace and study tools: direct, dense enough for daily use, and visually quiet.

## Layout
- Page shell uses a constrained content column on list pages and a wider working column on detail pages.
- Header contains the page title and the primary actions only.
- Classroom cards are repeated data items with a white surface, 1px border, 8px radius, and compact metadata.
- Detail pages use a header row with back navigation, title, role/member metadata, and action buttons.
- Tabs use a segmented control treatment, matching the study sidebar tab behavior.
- Overview panels and repeated assignment/member rows use border-led separation rather than large shadows.

## Modal Design
- Modals use a centered white surface, 8px radius, border, compact header, scroll-safe body, and sticky action footer where needed.
- Destructive actions use an in-app confirmation dialog with clear title, short body, and a red confirmation button.
- Browser-native `confirm()` and `alert()` should not appear in the primary classroom shell.

## Color And Type
- Primary blue: `#2563eb`.
- Hover blue: `#1d4ed8`.
- Text: `#0f172a`.
- Secondary text: `#475569`.
- Muted text: `#64748b`.
- Border: `#d7e2f0`.
- Background: `#f6f8fc`.
- Radius: 8px for cards, modals, tabs, and buttons.

## Responsive Behavior
- Header actions wrap cleanly on narrow screens.
- Classroom cards collapse to one column.
- Detail actions become full-width buttons on mobile.
- Modal body scrolls within the viewport instead of pushing action buttons off-screen.

## Implemented Surfaces
- Classroom list page.
- Classroom detail overview shell.
- Classroom tabs and repeated assignment/member cards.
- Create classroom and join classroom modals.
- Add member modal.
- Announcement creation/history/delete flows.
- Assignment creation/edit/detail/stats/retract flows.
- Classroom archive/delete/leave confirmation dialog.
