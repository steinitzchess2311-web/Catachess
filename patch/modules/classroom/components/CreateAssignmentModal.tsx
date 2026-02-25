import React, { useState } from 'react';
import { createAssignment } from '../api';
import type { Assignment, AssignmentCategory, AssignmentType } from '../types';

interface Props {
  classroomId: string;
  onClose: () => void;
  onCreated: (assignment: Assignment) => void;
}

export const CreateAssignmentModal: React.FC<Props> = ({ classroomId, onClose, onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<AssignmentCategory>('assignment');
  const [type, setType] = useState<AssignmentType>('tactics');
  const [dueDate, setDueDate] = useState('');
  const [maxAttempts, setMaxAttempts] = useState('');
  const [timeLimit, setTimeLimit] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const assignment = await createAssignment(classroomId, {
        title: title.trim(),
        description: description.trim() || undefined,
        category,
        type,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        max_attempts: maxAttempts ? parseInt(maxAttempts) : null,
        time_limit: timeLimit ? parseInt(timeLimit) * 60 : null,
        targets: { type: 'all' },
      });
      onCreated(assignment);
    } catch (err: any) {
      setError(err?.message || 'Failed to create assignment.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal cl-modal--wide" role="dialog" aria-modal="true" aria-labelledby="asgn-modal-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="asgn-modal-title">New Assignment</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="asgn-title">Title</label>
              <input
                id="asgn-title"
                className="cl-input"
                placeholder="e.g. Opening Homework #1"
                value={title}
                onChange={e => setTitle(e.target.value)}
                maxLength={200}
                autoFocus
                required
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-category">Category</label>
                <select id="asgn-category" className="cl-select" value={category} onChange={e => setCategory(e.target.value as AssignmentCategory)}>
                  <option value="material">Material</option>
                  <option value="assignment">Assignment</option>
                  <option value="exam">Exam</option>
                </select>
              </div>
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-type">Type</label>
                <select id="asgn-type" className="cl-select" value={type} onChange={e => setType(e.target.value as AssignmentType)}>
                  <option value="tactics">Tactics</option>
                  <option value="opening">Opening</option>
                  <option value="trainer">Trainer</option>
                  <option value="workspace">Workspace Study</option>
                  <option value="upload">Upload</option>
                </select>
              </div>
            </div>

            <div className="cl-field">
              <label className="cl-label" htmlFor="asgn-desc">Description (optional)</label>
              <textarea
                id="asgn-desc"
                className="cl-textarea"
                placeholder="Instructions for students…"
                value={description}
                onChange={e => setDescription(e.target.value)}
                rows={3}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-due">Due date</label>
                <input
                  id="asgn-due"
                  className="cl-input"
                  type="datetime-local"
                  value={dueDate}
                  onChange={e => setDueDate(e.target.value)}
                />
              </div>
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-attempts">Max attempts</label>
                <input
                  id="asgn-attempts"
                  className="cl-input"
                  type="number"
                  min="1"
                  placeholder="Unlimited"
                  value={maxAttempts}
                  onChange={e => setMaxAttempts(e.target.value)}
                />
              </div>
              <div className="cl-field">
                <label className="cl-label" htmlFor="asgn-timelimit">Time limit (min)</label>
                <input
                  id="asgn-timelimit"
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
              {loading ? 'Publishing…' : 'Publish'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
