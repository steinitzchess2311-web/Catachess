// ─── ActivityFeed — teacher overview, latest submission activity ──────────────

import React, { useEffect, useState } from 'react';
import { getActivity } from '../api';
import type { ActivityItem } from '../types';

interface Props {
  classroomId: string;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const ActivityFeed: React.FC<Props> = ({ classroomId }) => {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getActivity(classroomId)
      .then(data => setItems(data.slice(0, 12)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroomId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="cl-skeleton" style={{ height: 38, borderRadius: 8 }} />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div style={{ padding: '1.25rem 0', color: 'var(--cl-text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
        No submissions yet
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {items.map((item, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.7rem',
            padding: '0.55rem 0.7rem',
            borderRadius: 8,
            transition: 'background 0.12s',
          }}
          onMouseEnter={e => (e.currentTarget.style.background = 'var(--cl-bg)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
        >
          {/* Avatar */}
          <div className="cl-member-avatar" style={{ width: 28, height: 28, fontSize: '0.76rem', flexShrink: 0 }}>
            {item.username[0]?.toUpperCase()}
          </div>

          {/* Text */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{item.username}</span>
            <span style={{ color: 'var(--cl-text-secondary)', fontSize: '0.85rem' }}>
              {' '}{item.status === 'submitted' ? 'submitted' : 'started'}{' '}
            </span>
            <span
              style={{
                fontSize: '0.85rem',
                color: 'var(--cl-text)',
                fontWeight: 500,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: 200,
                display: 'inline-block',
                verticalAlign: 'bottom',
              }}
            >
              {item.assignment_title}
            </span>
          </div>

          {/* Score */}
          {item.score != null && (
            <span style={{
              fontSize: '0.78rem',
              fontWeight: 600,
              color: item.score >= 0.7 ? 'var(--cl-ok)' : item.score >= 0.5 ? 'var(--cl-soon)' : 'var(--cl-overdue)',
              flexShrink: 0,
            }}>
              {Math.round(item.score * 100)}%
            </span>
          )}

          {/* Time */}
          <span style={{ fontSize: '0.73rem', color: 'var(--cl-text-muted)', flexShrink: 0 }}>
            {timeAgo(item.submitted_at)}
          </span>
        </div>
      ))}
    </div>
  );
};
