// ─── Classroom Types ──────────────────────────────────────────────────────────

export type ClassroomRole = 'owner' | 'teacher' | 'student';

export interface Classroom {
  id: string;
  name: string;
  owner: string;
  my_role: ClassroomRole;
  member_count: number;
  archived_at: string | null;
  created_at: string;
  invite_code?: string;
  invite_active?: boolean;
  catchat_group_id?: string | null;
  workspace_folder_id?: string | null;
}

export interface ClassroomMember {
  username: string;
  role: ClassroomRole;
  joined_at: string;
  workspace_folder_id?: string | null;
}

// ─── Assignment Types ─────────────────────────────────────────────────────────

export type AssignmentCategory = 'material' | 'assignment' | 'exam';
export type AssignmentType = 'workspace' | 'upload' | 'tactics' | 'opening' | 'trainer';
export type SubmissionStatus = 'not_started' | 'in_progress' | 'submitted' | 'overdue';

export interface AssignmentTargets {
  type: 'all' | 'users';
  usernames?: string[];
}

export interface MySubmission {
  status: SubmissionStatus;
  score: number | null;
  attempt: number;
}

export interface Assignment {
  id: string;
  title: string;
  description?: string;
  category: AssignmentCategory;
  type: AssignmentType;
  source_type?: 'study' | 'lichess' | 'upload' | null;
  source_ref?: string | null;
  due_date: string | null;
  time_limit?: number | null;
  max_attempts?: number | null;
  created_at: string;
  targets?: AssignmentTargets;
  // Teacher view
  submission_count?: number;
  member_count?: number;
  // Student view
  my_submission?: MySubmission | null;
}

export interface AssignmentUpdatePayload {
  title?: string;
  description?: string;
  due_date?: string | null;
  time_limit?: number | null;
  max_attempts?: number | null;
}

export interface AssignmentCreatePayload {
  category: AssignmentCategory;
  type: AssignmentType;
  title: string;
  description?: string;
  source_type?: 'study' | 'lichess' | 'upload' | null;
  source_ref?: string | null;
  due_date?: string | null;
  time_limit?: number | null;
  max_attempts?: number | null;
  targets: AssignmentTargets;
}

// ─── Submission Types ─────────────────────────────────────────────────────────

export interface Submission {
  id: string;
  assignment_id: string;
  username: string;
  attempt: number;
  status: 'in_progress' | 'submitted';
  score: number | null;
  detail: Record<string, any> | null;
  started_at: string;
  submitted_at: string | null;
}

export interface SubmissionUpsertPayload {
  status: 'in_progress' | 'submitted';
  score?: number | null;
  detail?: Record<string, any>;
}

// ─── Stats ────────────────────────────────────────────────────────────────────

export interface AssignmentStats {
  assignment_id: string;
  total_targets: number;
  submitted: number;
  in_progress: number;
  not_started: number;
  overdue: number;
  avg_score: number | null;
  score_distribution: number[];
  per_student: Array<{
    username: string;
    status: SubmissionStatus;
    score: number | null;
    attempt: number;
    submitted_at: string | null;
  }>;
}

// ─── Activity ─────────────────────────────────────────────────────────────────

export interface ActivityItem {
  submission_id: string;
  student_username: string;
  assignment_id: string;
  assignment_title: string;
  assignment_category: string;
  attempt: number;
  status: 'submitted' | 'in_progress' | 'graded';
  score: number | null;
  submitted_at: string | null;
  started_at: string;
}

// ─── Todo ─────────────────────────────────────────────────────────────────────

export type TodoUrgency = 'overdue' | 'due_soon' | 'normal';

export interface TodoItem {
  assignment_id: string;
  title: string;
  category: AssignmentCategory;
  classroom_id?: string;
  classroom_name: string;
  due_date: string | null;
  urgency: TodoUrgency;
  my_status: 'not_started' | 'in_progress' | 'submitted';
}

// ─── Broadcast ────────────────────────────────────────────────────────────────

export interface BroadcastItem {
  id: string;
  sender_name: string;
  content: string;
  created_at: string;
}

// ─── Invite ───────────────────────────────────────────────────────────────────

export interface InviteInfo {
  invite_code: string;
  invite_active: boolean;
}
