// ─── BroadcastPanel — teacher view: manage sent announcements ─────────────────

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

  useEffect(() => {
    setLoading(true);
    listBroadcasts(classroomId, 5)
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroomId, refreshKey]);

  async function handleDelete(id: string) {
    if (!confirm('Delete this announcement?')) return;
    try {
      await deleteBroadcast(classroomId, id);
      setItems(prev => prev.filter(i => i.id !== id));
    } catch {
      alert('Failed to delete announcement.');
    }
  }

  return (
    <div>
      <div className="cl-section-header" style={{ marginBottom: '0.75rem' }}>
        <h3 className="cl-section-title">Announcements</h3>
        <span style={{ fontSize: '0.75rem', color: 'var(--cl-text-muted)' }}>last 5</span>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {[...Array(2)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 52, borderRadius: 8 }} />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p style={{ fontSize: '0.85rem', color: 'var(--cl-text-secondary)', margin: 0 }}>
          No announcements sent yet.
        </p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {items.map(item => (
            <div
              key={item.id}
              style={{
                background: 'var(--cl-surface)',
                border: '1.5px solid var(--cl-border)',
                borderRadius: 8,
                padding: '0.65rem 0.9rem',
                display: 'flex',
                gap: '0.75rem',
                alignItems: 'flex-start',
              }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{
                  margin: '0 0 4px',
                  fontSize: '0.87rem',
                  color: 'var(--cl-text)',
                  lineHeight: 1.45,
                  whiteSpace: 'pre-wrap',
                  overflow: 'hidden',
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                } as React.CSSProperties}>
                  {item.content}
                </p>
                <span style={{ fontSize: '0.73rem', color: 'var(--cl-text-muted)' }}>
                  {timeAgo(item.created_at)}
                </span>
              </div>
              <button
                className="cl-btn-icon"
                title="Delete announcement"
                onClick={() => handleDelete(item.id)}
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
    </div>
  );
};
