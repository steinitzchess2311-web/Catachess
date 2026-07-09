## header
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:20:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder.
  - Reusable classroom React components for modals, tabs, invite controls, member management, assignment management, broadcasts, badges, and sharing.
- 架构思路
  - Components receive classroom identifiers and typed data from page shells, call focused API helpers, and share product styling through `../classroom.css`.
  - Modal components use the shared `cl-modal` structure and should avoid ad hoc decorative inline styling.

## folder structure
|-ActivityFeed.tsx classroom activity list.
|-AddMemberModal.tsx product modal for searching and adding a classroom member.
|-AssignmentDetailModal.tsx assignment detail and submission modal.
|-AssignmentsTab.tsx assignments tab controller.
|-BroadcastBanner.tsx student-visible announcement banner.
|-BroadcastModal.tsx teacher broadcast creation modal.
|-BroadcastPanel.tsx teacher announcement history panel.
|-CategoryBadge.tsx assignment category badge.
|-CreateAssignmentModal.tsx assignment creation modal.
|-CreateClassroomModal.tsx classroom creation modal.
|-EditAssignmentModal.tsx assignment editing modal.
|-InvitePanel.tsx invite code panel.
|-JoinClassroomModal.tsx join classroom modal.
|-MembersTab.tsx member list and management tab.
|-OverviewTab.tsx legacy overview entry.
|-RoleBadge.tsx classroom role badge.
|-StatsModal.tsx assignment stats modal.
|-StatusBadge.tsx assignment status badge.
|-WorkspaceShareModal.tsx workspace-node sharing modal.
|-overview/ teacher/student overview components. Another README doc is necessary in this subfolder.

## 代办
- Continue reducing legacy inline styles when touching deep material and stats flows for functional work.
- Reduce remaining inline styles when touching each component for functional work.
