// ─── AddMemberModal — search user then add to classroom ──────────────────────

import React, { useState, useRef } from 'react';
import { api } from '@ui/assets/api';
import { addMember } from '../api';
import type { ClassroomMember, ClassroomRole } from '../types';

interface UserResult {
  id: string;
  username: string;
}

interface Props {
  classroomId: string;
  onClose: () => void;
  onAdded: (member: ClassroomMember) => void;
}

export const AddMemberModal: React.FC<Props> = ({ classroomId, onClose, onAdded }) => {
  const [query, setQuery]         = useState('');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [found, setFound]         = useState<UserResult | null>(null);
  const [role, setRole]           = useState<ClassroomRole>('student');
  const [adding, setAdding]       = useState(false);
  const [addError, setAddError]   = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setSearching(true);
    setSearchError('');
    setFound(null);
    setAddError('');
    try {
      const user = await api.get(`/user/by-username/${encodeURIComponent(q)}`);
      setFound(user as UserResult);
    } catch {
      setSearchError('User not found.');
    } finally {
      setSearching(false);
    }
  }

  async function handleAdd() {
    if (!found) return;
    setAdding(true);
    setAddError('');
    try {
      const member = await addMember(classroomId, found.username, found.id, role);
      onAdded(member);
    } catch (err: any) {
      setAddError(err?.message || 'Failed to add member.');
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal" role="dialog" aria-modal="true" aria-labelledby="add-member-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="add-member-title">Add Member</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        <div className="cl-modal__body">

          {/* Step 1 — Search */}
          <form onSubmit={handleSearch}>
            <div className="cl-field">
              <label className="cl-label" htmlFor="add-member-search">Search by username</label>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  id="add-member-search"
                  ref={inputRef}
                  className="cl-input"
                  placeholder="catachess username"
                  value={query}
                  onChange={e => { setQuery(e.target.value); setFound(null); setSearchError(''); setAddError(''); }}
                  autoFocus
                  autoComplete="off"
                  style={{ flex: 1 }}
                />
                <button
                  type="submit"
                  className="cl-btn cl-btn-secondary cl-btn-sm"
                  disabled={searching || !query.trim()}
                  style={{ flexShrink: 0 }}
                >
                  {searching ? 'Searching…' : 'Search'}
                </button>
              </div>
              {searchError && (
                <span style={{ fontSize: '0.78rem', color: 'var(--cl-overdue)', marginTop: 4, display: 'block' }}>
                  {searchError}
                </span>
              )}
            </div>
          </form>

          {/* Step 2 — Result + role + confirm */}
          {found && (
            <div style={{
              marginTop: '0.75rem',
              background: 'var(--cl-bg)',
              border: '1.5px solid var(--cl-border)',
              borderRadius: 10,
              padding: '0.85rem 1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
            }}>
              {/* Avatar */}
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: 'var(--cl-accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: '#fff', fontWeight: 700, fontSize: '0.9rem', flexShrink: 0,
              }}>
                {found.username[0].toUpperCase()}
              </div>

              <span style={{ fontSize: '0.9rem', fontWeight: 600, flex: 1 }}>{found.username}</span>

              {/* Role selector */}
              <select
                className="cl-select"
                value={role}
                onChange={e => setRole(e.target.value as ClassroomRole)}
                style={{ width: 110 }}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>

              {/* Add button */}
              <button
                className="cl-btn cl-btn-primary cl-btn-sm"
                onClick={handleAdd}
                disabled={adding}
                style={{ flexShrink: 0 }}
              >
                {adding ? 'Adding…' : 'Add'}
              </button>
            </div>
          )}

          {addError && <div className="cl-error-banner" style={{ marginTop: '0.5rem' }}>{addError}</div>}
        </div>

        <div className="cl-modal__footer">
          <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
