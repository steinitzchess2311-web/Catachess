/*
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex
*/

import React, { useEffect, useState } from 'react';
import { listBroadcasts, deleteBroadcast } from '../api';
import type { BroadcastItem } from '../types';

interface Props {
  classroomId: string;
  /** Called after a new broadcast is sent so we can refresh the list */
  refreshKey?: number;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const BroadcastPanel: React.FC<Props> = ({ classroomId, refreshKey }) => {
  const [items, setItems] = useState<BroadcastItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<BroadcastItem | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    listBroadcasts(classroomId, 5)
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroomId, refreshKey]);

  async function handleDelete(item: BroadcastItem) {
    if (!item.id) {
      setError('Announcement id is missing. Refresh and try again.');
      return;
    }
    setDeleteTarget(item);
  }

  async function confirmDelete() {
    if (!deleteTarget?.id) return;
    setDeleting(true);
    setError('');
    try {
      await deleteBroadcast(classroomId, deleteTarget.id);
      setItems(prev => prev.filter(i => i.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch {
      setError('Failed to delete announcement.');
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div>
      <div className="cl-section-header" style={{ marginBottom: '0.75rem' }}>
        <h3 className="cl-section-title">Announcements</h3>
      </div>
      {error && <div className="cl-error-banner" style={{ marginBottom: '0.75rem' }}>{error}</div>}

      {loading ? (
        <div className="cl-stack-loading">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 52, borderRadius: 8 }} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p style={{ fontSize: '0.85rem', color: 'var(--cl-text-secondary)', margin: 0 }}>
          No announcements sent yet.
        </p>
      ) : (
        <div className="cl-broadcast-list">
          {items.map(item => (
            <div
              key={item.id}
              className="cl-broadcast-item"
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <p className="cl-broadcast-copy">
                  {item.content}
                </p>
                <span className="cl-broadcast-time">
                  {timeAgo(item.created_at)}
                </span>
              </div>
              <button
                className="cl-btn-icon"
                title="Delete announcement"
                onClick={() => handleDelete(item)}
                style={{ color: 'var(--cl-text-muted)', flexShrink: 0, marginTop: 2 }}
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                  <path d="M10 11v6M14 11v6"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {deleteTarget && (
        <div className="cl-overlay" onClick={e => e.target === e.currentTarget && !deleting && setDeleteTarget(null)}>
          <div className="cl-modal cl-modal--confirm" role="dialog" aria-modal="true" aria-labelledby="delete-announcement-title">
            <div className="cl-modal__header">
              <h2 className="cl-modal__title" id="delete-announcement-title">Delete announcement</h2>
              <button className="cl-btn-icon" onClick={() => setDeleteTarget(null)} aria-label="Close" disabled={deleting}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            <div className="cl-modal__body">
              <p className="cl-confirm-copy">This announcement will be removed from the classroom.</p>
            </div>
            <div className="cl-modal__footer">
              <button className="cl-btn cl-btn-secondary" onClick={() => setDeleteTarget(null)} disabled={deleting}>Cancel</button>
              <button className="cl-btn cl-btn-danger" onClick={confirmDelete} disabled={deleting}>
                {deleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
