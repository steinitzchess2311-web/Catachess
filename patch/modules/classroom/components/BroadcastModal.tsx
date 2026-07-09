/*
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex
*/

import React, { useState } from 'react';
import { broadcastMessage } from '../api';

interface Props {
  classroomId: string;
  classroomName: string;
  onClose: () => void;
  onSent?: () => void;
}

export const BroadcastModal: React.FC<Props> = ({ classroomId, classroomName, onClose, onSent }) => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setLoading(true);
    setError('');
    try {
      await broadcastMessage(classroomId, content.trim());
      setSent(true);
      setTimeout(() => { onSent ? onSent() : onClose(); }, 1200);
    } catch (err: any) {
      setError(err?.message || 'Failed to send announcement.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal" role="dialog" aria-modal="true" aria-labelledby="broadcast-title">
        <div className="cl-modal__header">
          <div>
            <h2 className="cl-modal__title" id="broadcast-title">Announcement</h2>
          </div>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="cl-modal__body">
            <div className="cl-field">
              <label className="cl-label" htmlFor="broadcast-content">Message</label>
              <textarea
                id="broadcast-content"
                className="cl-textarea"
                placeholder={`Message ${classroomName}`}
                value={content}
                onChange={e => setContent(e.target.value)}
                rows={4}
                autoFocus
                required
              />
            </div>
            {error && <div className="cl-error-banner">{error}</div>}
            {sent && (
              <div className="cl-inline-success">
                Announcement sent
              </div>
            )}
          </div>
          <div className="cl-modal__footer">
            <button type="button" className="cl-btn cl-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="cl-btn cl-btn-primary" disabled={loading || !content.trim() || sent}>
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
