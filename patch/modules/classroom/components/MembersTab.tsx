import React, { useEffect, useState } from 'react';
import { listMembers, removeMember, updateMemberRole } from '../api';
import type { Classroom, ClassroomMember, ClassroomRole } from '../types';
import { RoleBadge } from './RoleBadge';
import { AddMemberModal } from './AddMemberModal';
import { InvitePanel } from './InvitePanel';
import { avatarColor } from '../utils';

interface Props {
  classroom: Classroom;
  onCountChange?: (count: number) => void;
}

export const MembersTab: React.FC<Props> = ({ classroom, onCountChange }) => {
  const [members, setMembers] = useState<ClassroomMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const canManage = classroom.my_role === 'owner' || classroom.my_role === 'teacher';
  const isOwner = classroom.my_role === 'owner';

  useEffect(() => {
    listMembers(classroom.id)
      .then(rows => {
        setMembers(rows);
        onCountChange?.(rows.length);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id, onCountChange]);

  async function handleRemove(username: string) {
    if (!confirm(`Remove ${username} from this classroom?`)) return;
    try {
      await removeMember(classroom.id, username);
      setMembers(prev => {
        const next = prev.filter(m => m.username !== username);
        onCountChange?.(next.length);
        return next;
      });
    } catch (err: any) {
      alert(err?.message || 'Failed to remove member.');
    }
  }

  async function handleRoleChange(username: string, newRole: ClassroomRole) {
    try {
      await updateMemberRole(classroom.id, username, newRole);
      setMembers(prev => prev.map(m => m.username === username ? { ...m, role: newRole } : m));
    } catch (err: any) {
      alert(err?.message || 'Failed to update role.');
    }
  }

  const teachers = members.filter(m => m.role === 'owner' || m.role === 'teacher');
  const students = members.filter(m => m.role === 'student');

  return (
    <div>
      {/* Invite panel */}
      {canManage && (
        <div style={{ marginBottom: '1.5rem' }}>
          <div className="cl-section-header" style={{ marginBottom: '0.6rem' }}>
            <h3 className="cl-section-title">Invite Link</h3>
          </div>
          <InvitePanel classroomId={classroom.id} canManage={canManage} />
        </div>
      )}

      {/* Members list */}
      <div className="cl-section-header">
        <h3 className="cl-section-title">Members ({members.length})</h3>
        {canManage && (
          <button className="cl-btn cl-btn-primary cl-btn-sm" onClick={() => setShowAddModal(true)}>
            + Add Member
          </button>
        )}
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 44, borderRadius: 6 }} />
          ))}
        </div>
      ) : members.length === 0 ? (
        <div className="cl-empty">
          <p className="cl-empty__title">No members yet</p>
          <p className="cl-empty__sub">Share the invite link to add students.</p>
        </div>
      ) : (
        <div>
          {/* Teachers section */}
          {teachers.length > 0 && (
            <>
              <p className="cl-section-label" style={{ marginTop: '0.5rem' }}>Teachers & Owners</p>
              <div className="cl-member-list" style={{ marginBottom: '1rem' }}>
                {teachers.map(m => (
                  <MemberRow
                    key={m.username}
                    member={m}
                    isOwner={isOwner}
                    currentUserIsOwner={isOwner}
                    canManage={canManage}
                    onRemove={handleRemove}
                    onRoleChange={handleRoleChange}
                  />
                ))}
              </div>
            </>
          )}
          {/* Students section */}
          {students.length > 0 && (
            <>
              <p className="cl-section-label">Students ({students.length})</p>
              <div className="cl-member-list">
                {students.map(m => (
                  <MemberRow
                    key={m.username}
                    member={m}
                    isOwner={isOwner}
                    currentUserIsOwner={isOwner}
                    canManage={canManage}
                    onRemove={handleRemove}
                    onRoleChange={handleRoleChange}
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {showAddModal && (
        <AddMemberModal
          classroomId={classroom.id}
          onClose={() => setShowAddModal(false)}
          onAdded={member => {
            setMembers(prev => {
              const next = [...prev, member];
              onCountChange?.(next.length);
              return next;
            });
            setShowAddModal(false);
          }}
        />
      )}
    </div>
  );
};

interface MemberRowProps {
  member: ClassroomMember;
  isOwner: boolean;
  currentUserIsOwner: boolean;
  canManage: boolean;
  onRemove: (username: string) => void;
  onRoleChange: (username: string, role: ClassroomRole) => void;
}

const MemberRow: React.FC<MemberRowProps> = ({ member, canManage, currentUserIsOwner, onRemove, onRoleChange }) => {
  const canEdit = canManage && member.role !== 'owner';

  return (
    <div className="cl-member-row">
      <div className="cl-member-avatar" style={{ background: avatarColor(member.username), color: '#fff' }}>
        {member.username?.[0]?.toUpperCase()}
      </div>
      <span className="cl-member-name">{member.username}</span>
      <RoleBadge role={member.role} />
      <span className="cl-member-joined">
        {new Date(member.joined_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
      </span>
      <div className="cl-member-actions">
        {member.workspace_folder_id && canManage && (
          <a
            href={`/workspace?folder=${member.workspace_folder_id}`}
            target="_blank"
            rel="noreferrer"
            className="cl-btn-icon"
            title="Open student workspace folder"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
            </svg>
          </a>
        )}
        {canEdit && currentUserIsOwner && (
          <button
            className="cl-btn-icon"
            title={member.role === 'student' ? 'Promote to teacher' : 'Demote to student'}
            onClick={() => onRoleChange(member.username, member.role === 'student' ? 'teacher' : 'student')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M17 3a2.828 2.828 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
            </svg>
          </button>
        )}
        {canEdit && (
          <button
            className="cl-btn-icon"
            title="Remove member"
            onClick={() => onRemove(member.username)}
            style={{ color: 'var(--cl-overdue)' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};
