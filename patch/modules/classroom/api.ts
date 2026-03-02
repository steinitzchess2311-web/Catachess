// ─── Classroom API ────────────────────────────────────────────────────────────
// Base: /api/classroom  (resolves to https://api.catachess.com in prod)

import { api } from '@ui/assets/api';
import type {
  Classroom,
  ClassroomMember,
  ClassroomRole,
  Assignment,
  AssignmentCreatePayload,
  AssignmentUpdatePayload,
  AssignmentStats,
  Submission,
  SubmissionUpsertPayload,
  ActivityItem,
  TodoItem,
  InviteInfo,
} from './types';

const BASE = '/api/classroom/classrooms';

// ─── Classrooms ───────────────────────────────────────────────────────────────

export const listClassrooms = (): Promise<Classroom[]> =>
  api.get(BASE);

export const getClassroom = (id: string): Promise<Classroom> =>
  api.get(`${BASE}/${id}`);

export const createClassroom = (name: string): Promise<Classroom> =>
  api.post(BASE, { name });

export const renameClassroom = (id: string, name: string): Promise<Classroom> =>
  api.patch(`${BASE}/${id}`, { name });

export const archiveClassroom = (id: string): Promise<void> =>
  api.post(`${BASE}/${id}/archive`, {});

export const unarchiveClassroom = (id: string): Promise<void> =>
  api.post(`${BASE}/${id}/unarchive`, {});

export const deleteClassroom = (id: string): Promise<void> =>
  api.delete(`${BASE}/${id}`);

// ─── Invite ───────────────────────────────────────────────────────────────────

export const getInvite = (id: string): Promise<InviteInfo> =>
  api.get(`${BASE}/${id}/invite`);

export const resetInvite = (id: string): Promise<InviteInfo> =>
  api.post(`${BASE}/${id}/invite/reset`, {});

export const setInviteActive = (id: string, active: boolean): Promise<InviteInfo> =>
  api.patch(`${BASE}/${id}/invite`, { active });

export const joinClassroom = (invite_code: string): Promise<Classroom> =>
  api.post(`${BASE}/join`, { invite_code });

// ─── Chat & Broadcast ─────────────────────────────────────────────────────────

export const getChatGroupId = (id: string): Promise<{ catchat_group_id: string | null }> =>
  api.get(`${BASE}/${id}/chat`);

export const broadcastMessage = (id: string, content: string): Promise<{ broadcast_id: string; created_at: string }> =>
  api.post(`${BASE}/${id}/broadcast`, { content });

export const listBroadcasts = async (id: string, limit = 5): Promise<import('./types').BroadcastItem[]> => {
  const rows = await api.get(`${BASE}/${id}/broadcasts?limit=${limit}`);
  if (!Array.isArray(rows)) return [];

  return rows
    .map((row: any) => ({
      // Backend currently returns broadcast_id/sender_username.
      id: row?.id ?? row?.broadcast_id ?? '',
      sender_name: row?.sender_name ?? row?.sender_username ?? 'Teacher',
      content: row?.content ?? '',
      created_at: row?.created_at ?? new Date().toISOString(),
    }))
    .filter((row: import('./types').BroadcastItem) => Boolean(row.id));
};

export const deleteBroadcast = (classroomId: string, messageId: string): Promise<void> =>
  api.delete(`${BASE}/${classroomId}/broadcasts/${messageId}`);

// ─── Members ──────────────────────────────────────────────────────────────────

export const listMembers = (classroomId: string): Promise<ClassroomMember[]> =>
  api.get(`${BASE}/${classroomId}/members`);

export const addMember = (classroomId: string, username: string, user_id: string, role: ClassroomRole = 'student'): Promise<ClassroomMember> =>
  api.post(`${BASE}/${classroomId}/members`, { username, user_id, role });

export const removeMember = (classroomId: string, username: string): Promise<void> =>
  api.delete(`${BASE}/${classroomId}/members/${username}`);

export const updateMemberRole = (classroomId: string, username: string, role: ClassroomRole): Promise<void> =>
  api.patch(`${BASE}/${classroomId}/members/${username}/role`, { role });

export const leaveClassroom = (classroomId: string): Promise<void> =>
  api.post(`${BASE}/${classroomId}/members/leave`, {});

// ─── Assignments ──────────────────────────────────────────────────────────────

export const listAssignments = (
  classroomId: string,
  params?: { category?: string; status?: string },
): Promise<Assignment[]> => {
  const query = params
    ? '?' + new URLSearchParams(
        Object.fromEntries(
          Object.entries(params).filter(([, v]) => v != null),
        ) as Record<string, string>,
      ).toString()
    : '';
  return api.get(`${BASE}/${classroomId}/assignments${query}`);
};

export const getAssignment = (classroomId: string, assignmentId: string): Promise<Assignment> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}`);

export const createAssignment = (classroomId: string, payload: AssignmentCreatePayload): Promise<Assignment> =>
  api.post(`${BASE}/${classroomId}/assignments`, payload);

export const updateAssignment = (classroomId: string, assignmentId: string, payload: AssignmentUpdatePayload): Promise<Assignment> =>
  api.patch(`${BASE}/${classroomId}/assignments/${assignmentId}`, payload);

export const deleteAssignment = (classroomId: string, assignmentId: string): Promise<void> =>
  api.delete(`${BASE}/${classroomId}/assignments/${assignmentId}`);

export const getAssignmentStats = (classroomId: string, assignmentId: string): Promise<AssignmentStats> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}/stats`);

// ─── Submissions ──────────────────────────────────────────────────────────────

export const upsertSubmission = (
  classroomId: string,
  assignmentId: string,
  payload: SubmissionUpsertPayload,
): Promise<Submission> =>
  api.post(`${BASE}/${classroomId}/assignments/${assignmentId}/submissions`, payload);

export const listSubmissions = (classroomId: string, assignmentId: string): Promise<Submission[]> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}/submissions`);

export const getMySubmission = (classroomId: string, assignmentId: string): Promise<Submission[]> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}/submissions/me`);

export const getStudentSubmission = (classroomId: string, assignmentId: string, username: string): Promise<Submission[]> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}/submissions/${username}`);

// ─── Activity ─────────────────────────────────────────────────────────────────

export const getActivity = (classroomId: string): Promise<ActivityItem[]> =>
  api.get(`${BASE}/${classroomId}/activity`);

// ─── Todo ─────────────────────────────────────────────────────────────────────

export const getMyTodo = (): Promise<TodoItem[]> =>
  api.get(`${BASE}/my/todo`);

// ─── Workspace Share ──────────────────────────────────────────────────────────

/**
 * Share a workspace node with the classroom teacher.
 *
 * Student-only action triggered from the classroom UI ("Share to Teacher").
 * The node stays in the student's private workspace; the teacher receives
 * viewer ACL and sees it in their workspace Shared section in real-time.
 *
 * This is distinct from the legacy workspace /share endpoint (which is still
 * available for direct workspace sharing).
 */
// ─── Material Forks ──────────────────────────────────────────────────────────

export const openMaterial = (
  classroomId: string,
  assignmentId: string,
): Promise<import('./types').OpenMaterialResponse> =>
  api.post(`${BASE}/${classroomId}/assignments/${assignmentId}/open-material`, {});

export const listForks = (
  classroomId: string,
  assignmentId: string,
): Promise<import('./types').MaterialFork[]> =>
  api.get(`${BASE}/${classroomId}/assignments/${assignmentId}/forks`);

// ─── Workspace Share ──────────────────────────────────────────────────────────

export const uploadMaterial = async (
  classroomId: string,
  assignmentId: string,
  file: File,
): Promise<{ ok: boolean; name: string; size: number }> => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post(`${BASE}/${classroomId}/assignments/${assignmentId}/upload-material`, formData);
};

export const downloadMaterialUrl = (classroomId: string, assignmentId: string): string =>
  `${BASE}/${classroomId}/assignments/${assignmentId}/download-material`;

export const shareToTeacher = (
  classroomId: string,
  nodeId: string,
): Promise<{ ok: boolean; message: string }> =>
  api.post(`${BASE}/${classroomId}/share-to-teacher`, { node_id: nodeId });
