import React, { useState } from 'react';
import { joinClassroom } from '../api';
import { useNavigate } from 'react-router-dom';

interface Props { onClose: () => void; }

export const JoinClassroomModal: React.FC<Props> = ({ onClose }) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) return;
    setLoading(true);
    setError('');
    try {
      const res = await joinClassroom(trimmed);
      navigate(`/classroom/${res.classroom_id}`);
    } catch (err: any) {
      setError(err?.message || 'Invalid or expired invite code.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal" role="dialog" aria-modal="true" aria-labelledby="join-modal-title">
        <div className="cl-modal__header">
          <h2 className="cl-modal__title" id="join-modal-title">Join a Classroom</h2>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="cl-join-code">Invite code</label>
              <input
                id="cl-join-code"
                className="cl-input"
                placeholder="e.g. ABC123"
                value={code}
                onChange={e => setCode(e.target.value.toUpperCase())}
                maxLength={16}
                autoFocus
                required
                style={{ textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 600 }}
              />
              <span className="cl-input-hint">Ask your teacher for the invite code.</span>
            </div>
            {error && <div className="cl-error-banner">{error}</div>}
          </div>
          <div className="cl-modal__footer">
            <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !code.trim()}>
              {loading ? 'Joining…' : 'Join'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
