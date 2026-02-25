// ─── Classroom API ────────────────────────────────────────────────────────────
// All calls hit /api/classroom (backend not yet live — returns placeholders gracefully)

import { api } from '@ui/assets/api';
import type {
  Classroom,
  ClassroomMember,
  ClassroomRole,
  Assignment,
  AssignmentCreatePayload,
  AssignmentStats,
  TodoItem,
  InviteInfo,
} from './types';

const BASE = '/api/classroom';

// ─── Classrooms ───────────────────────────────────────────────────────────────

export async function listClassrooms(): Promise<Classroom[]> {
  return api.get(`${BASE}/classrooms`);
}

export async function getClassroom(id: string): Promise<Classroom> {
  return api.get(`${BASE}/classrooms/${id}`);
}

export async function createClassroom(name: string): Promise<Classroom> {
  return api.post(`${BASE}/classrooms`, { name });
}

export async function renameClassroom(id: string, name: string): Promise<Classroom> {
  return api.patch(`${BASE}/classrooms/${id}`, { name });
}

export async function archiveClassroom(id: string): Promise<void> {
  return api.post(`${BASE}/classrooms/${id}/archive`, {});
}

export async function unarchiveClassroom(id: string): Promise<void> {
  return api.post(`${BASE}/classrooms/${id}/unarchive`, {});
}

export async function deleteClassroom(id: string): Promise<void> {
  return api.delete(`${BASE}/classrooms/${id}`);
}

// ─── Invite ───────────────────────────────────────────────────────────────────

export async function getInvite(id: string): Promise<InviteInfo> {
  return api.get(`${BASE}/classrooms/${id}/invite`);
}

export async function resetInvite(id: string): Promise<InviteInfo> {
  return api.post(`${BASE}/classrooms/${id}/invite/reset`, {});
}

export async function setInviteActive(id: string, active: boolean): Promise<InviteInfo> {
  return api.patch(`${BASE}/classrooms/${id}/invite`, { active });
}

export async function joinClassroom(invite_code: string): Promise<{ classroom_id: string; name: string; role: ClassroomRole }> {
  return api.post(`${BASE}/classrooms/join`, { invite_code });
}

// ─── Members ──────────────────────────────────────────────────────────────────

export async function listMembers(classroomId: string): Promise<ClassroomMember[]> {
  return api.get(`${BASE}/classrooms/${classroomId}/members`);
}

export async function addMember(classroomId: string, username: string, role: ClassroomRole = 'student'): Promise<ClassroomMember> {
  return api.post(`${BASE}/classrooms/${classroomId}/members`, { username, role });
}

export async function removeMember(classroomId: string, username: string): Promise<void> {
  return api.delete(`${BASE}/classrooms/${classroomId}/members/${username}`);
}

export async function updateMemberRole(classroomId: string, username: string, role: ClassroomRole): Promise<void> {
  return api.patch(`${BASE}/classrooms/${classroomId}/members/${username}/role`, { role });
}

export async function leaveClassroom(classroomId: string): Promise<void> {
  return api.post(`${BASE}/classrooms/${classroomId}/members/leave`, {});
}

// ─── Assignments ──────────────────────────────────────────────────────────────

export async function listAssignments(
  classroomId: string,
  params?: { category?: string; status?: string }
): Promise<Assignment[]> {
  const query = params
    ? '?' + new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v != null)) as Record<string, string>).toString()
    : '';
  return api.get(`${BASE}/classrooms/${classroomId}/assignments${query}`);
}

export async function getAssignment(classroomId: string, assignmentId: string): Promise<Assignment> {
  return api.get(`${BASE}/classrooms/${classroomId}/assignments/${assignmentId}`);
}

export async function createAssignment(classroomId: string, payload: AssignmentCreatePayload): Promise<Assignment> {
  return api.post(`${BASE}/classrooms/${classroomId}/assignments`, payload);
}

export async function deleteAssignment(classroomId: string, assignmentId: string): Promise<void> {
  return api.delete(`${BASE}/classrooms/${classroomId}/assignments/${assignmentId}`);
}

export async function getAssignmentStats(classroomId: string, assignmentId: string): Promise<AssignmentStats> {
  return api.get(`${BASE}/classrooms/${classroomId}/assignments/${assignmentId}/stats`);
}

// ─── Todo ─────────────────────────────────────────────────────────────────────

export async function getMyTodo(): Promise<TodoItem[]> {
  return api.get(`${BASE}/classrooms/my/todo`);
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export async function getChatGroupId(classroomId: string): Promise<{ catchat_group_id: string | null }> {
  return api.get(`${BASE}/classrooms/${classroomId}/chat`);
}

export async function broadcastMessage(classroomId: string, content: string): Promise<{ broadcast_id: string; created_at: string }> {
  return api.post(`${BASE}/classrooms/${classroomId}/broadcast`, { content });
}
