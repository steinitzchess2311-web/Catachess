import React, { useState } from 'react';
import { createClassroom } from '../api';
import type { Classroom } from '../types';

interface Props {
  onClose: () => void;
  onCreated: (classroom: Classroom) => void;
}

export const CreateClassroomModal: React.FC<Props> = ({ onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const classroom = await createClassroom(trimmed);
      onCreated(classroom);
    } catch (err: any) {
      setError(err?.message || 'Failed to create classroom.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal" role="dialog" aria-modal="true" aria-labelledby="create-modal-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="create-modal-title">New Classroom</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="cl-new-name">Classroom name</label>
              <input
                id="cl-new-name"
                className="cl-input"
                placeholder="e.g. Beginner Group A"
                value={name}
                onChange={e => setName(e.target.value)}
                maxLength={80}
                autoFocus
                required
              />
              <span className="cl-input-hint">A catachat group will be created automatically.</span>
            </div>
            {error && <div className="cl-error-banner">{error}</div>}
          </div>
          <div className="cl-modal__footer">
            <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !name.trim()}>
              {loading ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
