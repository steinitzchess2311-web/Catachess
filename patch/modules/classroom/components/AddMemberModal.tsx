import React, { useState } from 'react';
import { addMember } from '../api';
import type { ClassroomMember, ClassroomRole } from '../types';

interface Props {
  classroomId: string;
  onClose: () => void;
  onAdded: (member: ClassroomMember) => void;
}

export const AddMemberModal: React.FC<Props> = ({ classroomId, onClose, onAdded }) => {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState<ClassroomRole>('student');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = username.trim();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const member = await addMember(classroomId, trimmed, role);
      onAdded(member);
    } catch (err: any) {
      setError(err?.message || 'Failed to add member.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal" role="dialog" aria-modal="true" aria-labelledby="add-member-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="add-member-title">Add Member</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="member-username">Username</label>
              <input
                id="member-username"
                className="cl-input"
                placeholder="catachess username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div className="cl-field">
              <label className="cl-label" htmlFor="member-role">Role</label>
              <select
                id="member-role"
                className="cl-select"
                value={role}
                onChange={e => setRole(e.target.value as ClassroomRole)}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>
            </div>
            {error && <div className="cl-error-banner">{error}</div>}
          </div>
          <div className="cl-modal__footer">
            <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !username.trim()}>
              {loading ? 'Adding…' : 'Add'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
