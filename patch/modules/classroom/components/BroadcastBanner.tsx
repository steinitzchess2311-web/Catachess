// ─── BroadcastBanner — student view: shows latest announcements from teacher ──

import React, { useEffect, useState } from 'react';
import { listBroadcasts } from '../api';
import type { BroadcastItem } from '../types';

interface Props {
  classroomId: string;
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

export const BroadcastBanner: React.FC<Props> = ({ classroomId }) => {
  const [items, setItems] = useState<BroadcastItem[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listBroadcasts(classroomId, 5)
      .then(setItems)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroomId]);

  if (loading || items.length === 0) return null;

  const latest = items[0];
  const rest = items.slice(1);

  return (
    <div style={{
      background: 'linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%)',
      border: '1.5px solid #c7d2fe',
      borderRadius: 12,
      overflow: 'hidden',
    }}>
      {/* Latest announcement — always visible */}
      <div style={{ padding: '1rem 1.1rem', display: 'flex', gap: '0.85rem', alignItems: 'flex-start' }}>
        {/* Megaphone icon */}
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: 'var(--cl-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, marginTop: 1,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 11l18-5-5 18-5-8-8-5z"/>
          </svg>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: 4 }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--cl-accent)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
              Announcement
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--cl-text-muted)' }}>
              from {latest.sender_name} · {timeAgo(latest.created_at)}
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '0.92rem', fontWeight: 500, color: 'var(--cl-text)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
            {latest.content}
          </p>
        </div>
      </div>

      {/* History toggle */}
      {rest.length > 0 && (
        <>
          <button
            onClick={() => setExpanded(o => !o)}
            style={{
              width: '100%',
              background: 'none',
              border: 'none',
              borderTop: '1px solid #c7d2fe',
              padding: '0.55rem 1.1rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              cursor: 'pointer',
              color: 'var(--cl-accent)',
              fontSize: '0.78rem',
              fontWeight: 600,
            }}
          >
            <svg
              width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
              style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.15s' }}
            >
              <polyline points="6 9 12 15 18 9"/>
            </svg>
            {expanded ? 'Hide' : `${rest.length} older announcement${rest.length > 1 ? 's' : ''}`}
          </button>

          {expanded && (
            <div style={{ borderTop: '1px solid #c7d2fe' }}>
              {rest.map(item => (
                <div
                  key={item.id}
                  style={{
                    padding: '0.75rem 1.1rem 0.75rem 3.1rem',
                    borderBottom: '1px solid #e0e7ff',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 3,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '0.72rem', color: 'var(--cl-text-muted)' }}>
                      {item.sender_name} · {timeAgo(item.created_at)}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.87rem', color: 'var(--cl-text-secondary)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
                    {item.content}
                  </p>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
