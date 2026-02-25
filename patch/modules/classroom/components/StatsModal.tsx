import React, { useEffect, useState } from 'react';
import { getAssignmentStats } from '../api';
import type { AssignmentStats, Assignment } from '../types';
import { StatusBadge } from './StatusBadge';

interface Props {
  classroomId: string;
  assignment: Assignment;
  onClose: () => void;
}

export const StatsModal: React.FC<Props> = ({ classroomId, assignment, onClose }) => {
  const [stats, setStats] = useState<AssignmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAssignmentStats(classroomId, assignment.id)
      .then(setStats)
      .catch(err => setError(err?.message || 'Failed to load stats.'))
      .finally(() => setLoading(false));
  }, [classroomId, assignment.id]);

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal cl-modal--wide" role="dialog" aria-modal="true" aria-labelledby="stats-modal-title"
           style={{ maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="cl-modal__header">
          <div>
            <h2 className="cl-modal__title" id="stats-modal-title">Submission Stats</h2>
            <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: 'var(--cl-text-secondary)' }}>{assignment.title}</p>
          </div>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="cl-skeleton" style={{ height: 20, borderRadius: 6 }} />
              ))}
            </div>
          )}

          {error && <div className="cl-error-banner">{error}</div>}

          {stats && (
            <>
              {/* Overview chips */}
              <div className="cl-stats-overview">
                <div className="cl-stat-chip cl-stat-chip--submitted">
                  <span className="cl-stat-chip__value">{stats.submitted}</span>
                  <span className="cl-stat-chip__label">Submitted</span>
                </div>
                <div className="cl-stat-chip cl-stat-chip--accent">
                  <span className="cl-stat-chip__value">{stats.in_progress}</span>
                  <span className="cl-stat-chip__label">In Progress</span>
                </div>
                <div className="cl-stat-chip">
                  <span className="cl-stat-chip__value">{stats.not_started}</span>
                  <span className="cl-stat-chip__label">Not Started</span>
                </div>
                <div className="cl-stat-chip cl-stat-chip--overdue">
                  <span className="cl-stat-chip__value">{stats.overdue}</span>
                  <span className="cl-stat-chip__label">Overdue</span>
                </div>
                {stats.avg_score != null && (
                  <div className="cl-stat-chip cl-stat-chip--accent">
                    <span className="cl-stat-chip__value">{Math.round(stats.avg_score * 100)}%</span>
                    <span className="cl-stat-chip__label">Avg Score</span>
                  </div>
                )}
              </div>

              {/* Per-student table */}
              {stats.per_student.length > 0 && (
                <div>
                  <p className="cl-section-label" style={{ marginBottom: '0.6rem' }}>Per Student</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {stats.per_student.map(s => (
                      <div key={s.username} style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        padding: '0.5rem 0.6rem',
                        borderRadius: 6,
                        background: 'var(--cl-bg)',
                      }}>
                        <div className="cl-member-avatar" style={{ width: 28, height: 28, fontSize: '0.78rem' }}>
                          {s.username[0]?.toUpperCase()}
                        </div>
                        <span style={{ flex: 1, fontSize: '0.85rem', fontWeight: 500 }}>{s.username}</span>
                        <StatusBadge status={s.status as any} />
                        {s.score != null && (
                          <span style={{ fontSize: '0.82rem', color: 'var(--cl-text-secondary)', minWidth: 40, textAlign: 'right' }}>
                            {Math.round(s.score * 100)}%
                          </span>
                        )}
                        {s.submitted_at && (
                          <span style={{ fontSize: '0.75rem', color: 'var(--cl-text-muted)' }}>
                            {new Date(s.submitted_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="cl-modal__footer">
          <button className="cl-btn cl-btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
