/*
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex
*/

import React, { useEffect, useState } from 'react';
import { getAssignmentStats, listForks, downloadMaterialUrl } from '../api';
import type { AssignmentStats, Assignment, MaterialFork } from '../types';
import { StatusBadge } from './StatusBadge';
import { avatarColor } from '../utils';

interface Props {
  classroomId: string;
  assignment: Assignment;
  onClose: () => void;
}

interface UploadEntry { key: string; name: string; size?: number; content_type?: string }

function parseSourceRef(ref: string | null | undefined): { study_id?: string; uploads: UploadEntry[] } {
  if (!ref) return { uploads: [] };
  try {
    const parsed = JSON.parse(ref);
    if (parsed.uploads) return { study_id: parsed.study_id, uploads: parsed.uploads };
    if (parsed.key) return { uploads: [parsed as UploadEntry] };
    if (parsed.study_id) return { study_id: parsed.study_id, uploads: [] };
    return { uploads: [] };
  } catch {
    return { study_id: ref, uploads: [] };
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const StatsModal: React.FC<Props> = ({ classroomId, assignment, onClose }) => {
  const [stats, setStats] = useState<AssignmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [forks, setForks] = useState<MaterialFork[]>([]);
  const [forksLoading, setForksLoading] = useState(false);

  const isMaterial = assignment.category === 'material';
  const sourceInfo = isMaterial ? parseSourceRef(assignment.source_ref) : { uploads: [] };
  const hasStudy = isMaterial && (assignment.source_type === 'study' || !!sourceInfo.study_id);
  const isStudyMaterial = hasStudy;
  const uploads = sourceInfo.uploads;

  useEffect(() => {
    getAssignmentStats(classroomId, assignment.id)
      .then(setStats)
      .catch(err => setError(err?.message || 'Failed to load stats.'))
      .finally(() => setLoading(false));
  }, [classroomId, assignment.id]);

  useEffect(() => {
    if (!isStudyMaterial) return;
    setForksLoading(true);
    listForks(classroomId, assignment.id)
      .then(setForks)
      .catch(() => {})
      .finally(() => setForksLoading(false));
  }, [classroomId, assignment.id, isStudyMaterial]);

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="cl-modal cl-modal--wide" role="dialog" aria-modal="true" aria-labelledby="stats-modal-title"
           style={{ maxHeight: '85vh', display: 'flex', flexDirection: 'column' }}>
        <div className="cl-modal__header">
          <div>
            <h2 className="cl-modal__title" id="stats-modal-title">Submission stats</h2>
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

          {isMaterial && (
            <div style={{ marginBottom: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {hasStudy && (
                <div>
                  <p className="cl-section-label" style={{ marginBottom: '0.4rem' }}>Workspace study</p>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '0.6rem',
                    background: 'var(--cl-bg)',
                    border: '1px solid var(--cl-border, #e2e8f0)',
                    borderRadius: 8,
                    padding: '0.6rem 0.8rem',
                  }}>
                    <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 500 }}>Workspace study</p>
                  </div>
                </div>
              )}

              {uploads.length > 0 && (
                <div>
                  <p className="cl-section-label" style={{ marginBottom: '0.4rem' }}>Uploaded materials</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {uploads.map((u, i) => (
                      <div key={u.key || i} style={{
                        display: 'flex', alignItems: 'center', gap: '0.6rem',
                        background: 'var(--cl-bg)',
                        border: '1px solid var(--cl-border, #e2e8f0)',
                        borderRadius: 8,
                        padding: '0.6rem 0.8rem',
                      }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {u.name || 'Uploaded file'}
                          </p>
                          {u.size != null && (
                            <p style={{ margin: 0, fontSize: '0.72rem', color: 'var(--cl-text-muted)' }}>{formatSize(u.size)}</p>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }}>
                          <button
                            className="cl-btn cl-btn-secondary cl-btn-sm"
                            onClick={async () => {
                              const url = downloadMaterialUrl(classroomId, assignment.id, { preview: true, fileKey: u.key });
                              const res = await fetch(url, { credentials: 'include' });
                              if (res.ok) {
                                const blob = await res.blob();
                                window.open(URL.createObjectURL(blob), '_blank');
                              }
                            }}
                          >
                            Open
                          </button>
                          <button
                            className="cl-btn cl-btn-secondary cl-btn-sm"
                            onClick={async () => {
                              const url = downloadMaterialUrl(classroomId, assignment.id, { fileKey: u.key });
                              const res = await fetch(url, { credentials: 'include' });
                              if (res.ok) {
                                const blob = await res.blob();
                                const a = document.createElement('a');
                                a.href = URL.createObjectURL(blob);
                                a.download = u.name || 'download';
                                a.click();
                                URL.revokeObjectURL(a.href);
                              }
                            }}
                          >
                            Download
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {!hasStudy && uploads.length === 0 && (
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--cl-text-muted)' }}>
                  No material source attached.
                </p>
              )}
            </div>
          )}

          {stats && (
            <>
              <div className="cl-stats-overview">
                {isMaterial ? (
                  <>
                    <div className="cl-stat-chip cl-stat-chip--submitted">
                      <span className="cl-stat-chip__value">{stats.submitted}</span>
                      <span className="cl-stat-chip__label">Done</span>
                    </div>
                    <div className="cl-stat-chip">
                      <span className="cl-stat-chip__value">{stats.not_started + stats.in_progress}</span>
                      <span className="cl-stat-chip__label">Undone</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="cl-stat-chip cl-stat-chip--submitted">
                      <span className="cl-stat-chip__value">{stats.submitted}</span>
                      <span className="cl-stat-chip__label">Submitted</span>
                    </div>
                    <div className="cl-stat-chip cl-stat-chip--accent">
                      <span className="cl-stat-chip__value">{stats.in_progress}</span>
                      <span className="cl-stat-chip__label">In progress</span>
                    </div>
                    <div className="cl-stat-chip">
                      <span className="cl-stat-chip__value">{stats.not_started}</span>
                      <span className="cl-stat-chip__label">Not started</span>
                    </div>
                    <div className="cl-stat-chip cl-stat-chip--overdue">
                      <span className="cl-stat-chip__value">{stats.overdue}</span>
                      <span className="cl-stat-chip__label">Overdue</span>
                    </div>
                    {stats.avg_score != null && (
                      <div className="cl-stat-chip cl-stat-chip--accent">
                        <span className="cl-stat-chip__value">{Math.round(stats.avg_score * 100)}%</span>
                        <span className="cl-stat-chip__label">Avg score</span>
                      </div>
                    )}
                  </>
                )}
              </div>

              {stats.per_student.length > 0 && (
                <div>
                  <p className="cl-section-label" style={{ marginBottom: '0.6rem' }}>Per student</p>
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
                        <div className="cl-member-avatar" style={{ width: 28, height: 28, fontSize: '0.78rem', background: avatarColor(s.username), color: '#fff' }}>
                          {s.username?.[0]?.toUpperCase()}
                        </div>
                        <span style={{ flex: 1, fontSize: '0.85rem', fontWeight: 500 }}>{s.username}</span>
                        <StatusBadge status={s.status as any} isMaterial={isMaterial} />
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

          {isStudyMaterial && (
            <div style={{ marginTop: '1.25rem' }}>
              <p className="cl-section-label" style={{ marginBottom: '0.6rem' }}>Student forks</p>
              {forksLoading ? (
                <div className="cl-skeleton" style={{ height: 32, borderRadius: 6 }} />
              ) : forks.length === 0 ? (
                <p style={{ fontSize: '0.85rem', color: 'var(--cl-text-muted)' }}>No students have opened this material yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {forks.map(f => (
                    <div key={f.student_username} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.5rem 0.6rem',
                      borderRadius: 6,
                      background: 'var(--cl-bg)',
                    }}>
                      <div className="cl-member-avatar" style={{ width: 28, height: 28, fontSize: '0.78rem', background: avatarColor(f.student_username), color: '#fff' }}>
                        {f.student_username?.[0]?.toUpperCase()}
                      </div>
                      <span style={{ flex: 1, fontSize: '0.85rem', fontWeight: 500 }}>{f.student_username}</span>
                      <a
                        href={`/workspace/shared/classroom/study/${f.fork_study_id}?mode=material`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="cl-btn cl-btn-secondary cl-btn-sm"
                        style={{ textDecoration: 'none' }}
                        onClick={e => e.stopPropagation()}
                      >
                        View Fork
                      </a>
                      <span style={{ fontSize: '0.73rem', color: 'var(--cl-text-muted)' }}>
                        {f.created_at ? new Date(f.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="cl-modal__footer">
          <button className="cl-btn cl-btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
