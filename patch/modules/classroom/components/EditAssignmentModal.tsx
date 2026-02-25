// ─── EditAssignmentModal — teacher edits an existing assignment ───────────────

import React, { useState } from 'react';
import { updateAssignment } from '../api';
import type { Assignment } from '../types';

interface Props {
  classroomId: string;
  assignment: Assignment;
  onClose: () => void;
  onUpdated: (updated: Assignment) => void;
}

// Local helper: ISO datetime string → datetime-local input value
function toLocalInput(iso: string | null | undefined): string {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export const EditAssignmentModal: React.FC<Props> = ({ classroomId, assignment, onClose, onUpdated }) => {
  const [title, setTitle] = useState(assignment.title);
  const [description, setDescription] = useState(assignment.description ?? '');
  const [dueDate, setDueDate] = useState(toLocalInput(assignment.due_date));
  const [maxAttempts, setMaxAttempts] = useState(
    assignment.max_attempts != null ? String(assignment.max_attempts) : '',
  );
  const [timeLimit, setTimeLimit] = useState(
    assignment.time_limit != null ? String(Math.floor(assignment.time_limit / 60)) : '',
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    setError('');
    try {
      const updated = await updateAssignment(classroomId, assignment.id, {
        title: title.trim(),
        description: description.trim() || undefined,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        max_attempts: maxAttempts ? parseInt(maxAttempts) : null,
        time_limit: timeLimit ? parseInt(timeLimit) * 60 : null,
      });
      onUpdated(updated);
    } catch (err: any) {
      setError(err?.message || 'Failed to update assignment.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal cl-modal--wide" role="dialog" aria-modal="true" aria-labelledby="edit-asgn-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="edit-asgn-title">Edit Assignment</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="edit-title">Title</label>
              <input
                id="edit-title"
                className="cl-input"
                value={title}
                onChange={e => setTitle(e.target.value)}
                maxLength={200}
                required
                autoFocus
              />
            </div>
            <div className="cl-field">
              <label className="cl-label" htmlFor="edit-desc">Description</label>
              <textarea
                id="edit-desc"
                className="cl-textarea"
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
                placeholder="Instructions for students…"
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
              <div className="cl-field">
                <label className="cl-label" htmlFor="edit-due">Due date</label>
                <input
                  id="edit-due"
                  className="cl-input"
                  type="datetime-local"
                  value={dueDate}
                  onChange={e => setDueDate(e.target.value)}
                />
              </div>
              <div className="cl-field">
                <label className="cl-label" htmlFor="edit-attempts">Max attempts</label>
                <input
                  id="edit-attempts"
                  className="cl-input"
                  type="number"
                  min="1"
                  placeholder="Unlimited"
                  value={maxAttempts}
                  onChange={e => setMaxAttempts(e.target.value)}
                />
              </div>
              <div className="cl-field">
                <label className="cl-label" htmlFor="edit-time">Time limit (min)</label>
                <input
                  id="edit-time"
                  className="cl-input"
                  type="number"
                  min="1"
                  placeholder="None"
                  value={timeLimit}
                  onChange={e => setTimeLimit(e.target.value)}
                />
              </div>
            </div>
            {error && <div className="cl-error-banner">{error}</div>}
          </div>
          <div className="cl-modal__footer">
            <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !title.trim()}>
              {loading ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
