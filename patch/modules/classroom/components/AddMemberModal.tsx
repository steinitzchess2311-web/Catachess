/*
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex
*/

import React, { useState, useRef } from 'react';
import { api } from '@ui/assets/api';
import { addMember } from '../api';
import type { ClassroomMember, ClassroomRole } from '../types';
import { avatarColor } from '../utils';

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

          <form onSubmit={handleSearch}>
            <div className="cl-field">
              <label className="cl-label" htmlFor="add-member-search">Search by username</label>
              <div className="cl-inline-row">
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
                  {searching ? 'Searching...' : 'Search'}
                </button>
              </div>
              {searchError && (
                <span className="cl-inline-error">
                  {searchError}
                </span>
              )}
            </div>
          </form>

          {found && (
            <div className="cl-user-result">
              <div
                className="cl-user-result__avatar"
                style={{ background: found.username ? avatarColor(found.username) : 'var(--cl-accent)' }}
              >
                {found.username?.[0]?.toUpperCase()}
              </div>

              <span className="cl-user-result__name">{found.username}</span>

              <select
                className="cl-select"
                value={role}
                onChange={e => setRole(e.target.value as ClassroomRole)}
                style={{ width: 110 }}
              >
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>

              <button
                className="cl-btn cl-btn-primary cl-btn-sm"
                onClick={handleAdd}
                disabled={adding}
                style={{ flexShrink: 0 }}
              >
                {adding ? 'Adding...' : 'Add'}
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
