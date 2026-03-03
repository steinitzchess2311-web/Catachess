// ─── AssignmentDetailModal — student view: full details + submission flow ─────

import React, { useEffect, useState } from 'react';
import { upsertSubmission, getMySubmission, openMaterial, downloadMaterialUrl } from '../api';
import type { Assignment, Submission } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { StatusBadge } from './StatusBadge';
import { formatDue, dueCssModifier } from '../utils';

interface Props {
  classroomId: string;
  assignment: Assignment;
  onClose: () => void;
  onSubmitted: () => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface UploadEntry { key: string; name: string; size?: number; content_type?: string }

function parseSourceRef(ref: string | null | undefined): { study_id?: string; uploads: UploadEntry[] } {
  if (!ref) return { uploads: [] };
  try {
    const parsed = JSON.parse(ref);
    // New multi-upload format: { study_id?, uploads: [...] }
    if (parsed.uploads) return { study_id: parsed.study_id, uploads: parsed.uploads };
    // Legacy single-upload format: { key, name, size, content_type }
    if (parsed.key) return { uploads: [parsed as UploadEntry] };
    // Study-only format: { study_id }
    if (parsed.study_id) return { study_id: parsed.study_id, uploads: [] };
    // Plain string study_id (oldest format)
    return { uploads: [] };
  } catch {
    // source_ref is a plain study ID string
    return { study_id: ref, uploads: [] };
  }
}

export const AssignmentDetailModal: React.FC<Props> = ({
  classroomId,
  assignment,
  onClose,
  onSubmitted,
}) => {
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [loadingSubs, setLoadingSubs] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [openingStudy, setOpeningStudy] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null); // key of file being previewed/downloaded

  const isMaterial = assignment.category === 'material';
  const sourceInfo = isMaterial ? parseSourceRef(assignment.source_ref) : { uploads: [] };
  const hasStudy = isMaterial && (assignment.source_type === 'study' || !!sourceInfo.study_id);
  const uploads = sourceInfo.uploads;
  const [markedDone, setMarkedDone] = useState(false);
  const isInstructionsOnly = isMaterial && !hasStudy && uploads.length === 0;

  // ── Auto-mark material as done on first interaction ─────────────────
  function markMaterialDone() {
    if (!isMaterial || markedDone) return;
    setMarkedDone(true);
    upsertSubmission(classroomId, assignment.id, { status: 'submitted' })
      .then(() => onSubmitted())
      .catch(() => {}); // best-effort
  }

  // Instructions-only materials: auto-submit on open (read = done)
  useEffect(() => {
    if (isInstructionsOnly && !markedDone) markMaterialDone();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isInstructionsOnly]);

  // ── Study: call open-material API → share ACL → open new tab ──────────
  async function handleOpenStudy() {
    if (openingStudy) return;
    setOpeningStudy(true);
    setError('');
    try {
      const res = await openMaterial(classroomId, assignment.id);
      const studyId = res.study_id || res.fork_study_id;
      // Open in new browser window — precise navigation to study page
      window.open(`/workspace/shared/classroom/${studyId}`, '_blank');
      markMaterialDone();
    } catch (err: any) {
      setError(err?.message || 'Failed to open study.');
    } finally {
      setOpeningStudy(false);
    }
  }

  // ── Upload: preview in new window (fetch with auth → blob URL) ───────
  async function handlePreview(upload: UploadEntry) {
    if (busyKey) return;
    setBusyKey(upload.key);
    setError('');
    try {
      const url = downloadMaterialUrl(classroomId, assignment.id, { preview: true, fileKey: upload.key });
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load file');
      const blob = await res.blob();
      window.open(URL.createObjectURL(blob), '_blank');
      markMaterialDone();
    } catch (err: any) {
      setError(err?.message || 'Failed to preview file.');
    } finally {
      setBusyKey(null);
    }
  }

  // ── Upload: download file ──────────────────────────────────────────────
  async function handleDownload(upload: UploadEntry) {
    if (busyKey) return;
    setBusyKey(upload.key);
    setError('');
    try {
      const url = downloadMaterialUrl(classroomId, assignment.id, { fileKey: upload.key });
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = upload.name || 'download';
      a.click();
      URL.revokeObjectURL(a.href);
      markMaterialDone();
    } catch (err: any) {
      setError(err?.message || 'Failed to download file.');
    } finally {
      setBusyKey(null);
    }
  }

  const latestSub = submissions[submissions.length - 1] ?? null;
  const alreadySubmitted = latestSub?.status === 'submitted';
  const attemptCount = submissions.length;
  const maxAttempts = assignment.max_attempts ?? null;
  const canRetry = !alreadySubmitted || (maxAttempts === null ? true : attemptCount < maxAttempts);
  const isOverdue = assignment.due_date ? new Date(assignment.due_date) < new Date() : false;

  useEffect(() => {
    if (isMaterial) { setLoadingSubs(false); return; } // materials have no submissions
    setLoadingSubs(true);
    getMySubmission(classroomId, assignment.id)
      .then(setSubmissions)
      .catch(() => setSubmissions([]))
      .finally(() => setLoadingSubs(false));
  }, [classroomId, assignment.id, isMaterial]);

  async function handleSubmit() {
    setSubmitting(true);
    setError('');
    try {
      await upsertSubmission(classroomId, assignment.id, { status: 'submitted' });
      onSubmitted();
      onClose();
    } catch (err: any) {
      setError(err?.message || 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleStartProgress() {
    try {
      await upsertSubmission(classroomId, assignment.id, { status: 'in_progress' });
      setSubmissions(prev => [...prev, {
        id: '',
        assignment_id: assignment.id,
        username: '',
        attempt: attemptCount + 1,
        status: 'in_progress',
        score: null,
        detail: null,
        started_at: new Date().toISOString(),
        submitted_at: null,
      }]);
    } catch {
      // silent
    }
  }

  const dueModifier = assignment.due_date ? dueCssModifier(assignment.due_date) : 'normal';

  return (
    <div className="cl-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div
        className="cl-modal cl-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="asgn-detail-title"
        style={{ maxHeight: '88vh', display: 'flex', flexDirection: 'column' }}
      >
        {/* Header */}
        <div className="cl-modal__header">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <CategoryBadge category={assignment.category} />
              {assignment.type && (
                <span style={{ fontSize: '0.75rem', color: 'var(--cl-text-muted)', textTransform: 'capitalize' }}>
                  {assignment.type}
                </span>
              )}
            </div>
            <h2 className="cl-modal__title" id="asgn-detail-title" style={{ fontSize: '1.1rem', marginTop: 2 }}>
              {assignment.title}
            </h2>
          </div>
          <button className="cl-btn-icon" onClick={onClose} aria-label="Close" style={{ flexShrink: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Meta row */}
          <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
            {assignment.due_date && (
              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 3px' }}>Due</p>
                <p className={`cl-asgn-card__due cl-asgn-card__due--${dueModifier}`} style={{ margin: 0, fontSize: '0.88rem', fontWeight: 600 }}>
                  {new Date(assignment.due_date).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            )}
            {assignment.time_limit != null && assignment.time_limit > 0 && (
              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 3px' }}>Time Limit</p>
                <p style={{ margin: 0, fontSize: '0.88rem', fontWeight: 600 }}>{Math.floor(assignment.time_limit / 60)} min</p>
              </div>
            )}
            {assignment.max_attempts != null && assignment.max_attempts > 0 && (
              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 3px' }}>Attempts</p>
                <p style={{ margin: 0, fontSize: '0.88rem', fontWeight: 600 }}>{attemptCount} / {assignment.max_attempts}</p>
              </div>
            )}
          </div>

          {/* Description */}
          {assignment.description && (
            <div>
              <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 6px' }}>Instructions</p>
              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--cl-text)', whiteSpace: 'pre-wrap' }}>
                {assignment.description}
              </p>
            </div>
          )}

          {/* ── Material section ─────────────────────────────────────────── */}
          {isMaterial && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {/* Study material (top) */}
              {hasStudy && (
                <div>
                  <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 8px' }}>Workspace Study</p>
                  <div
                    onClick={handleOpenStudy}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.7rem',
                      background: 'var(--cl-surface, #f8fafc)',
                      border: '1.5px solid var(--cl-border, #e2e8f0)',
                      borderRadius: 10,
                      padding: '0.85rem 1rem',
                      cursor: openingStudy ? 'wait' : 'pointer',
                      transition: 'border-color 0.15s',
                    }}
                    onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--cl-accent, #3b82f6)')}
                    onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--cl-border, #e2e8f0)')}
                  >
                    <span style={{ fontSize: '1.5rem', flexShrink: 0 }}>📖</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>Workspace Study</p>
                      <p style={{ margin: '2px 0 0', fontSize: '0.76rem', color: 'var(--cl-text-muted)' }}>Click to open in new tab</p>
                    </div>
                    <span style={{ fontSize: '0.85rem', color: 'var(--cl-accent, #3b82f6)', fontWeight: 600, flexShrink: 0 }}>
                      {openingStudy ? 'Opening…' : 'Open →'}
                    </span>
                  </div>
                </div>
              )}

              {/* Uploaded materials (bottom) — only shown when uploads exist */}
              {uploads.length > 0 && (
                <div>
                  <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 8px' }}>Uploaded Materials</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {uploads.map((u, i) => (
                      <div
                        key={u.key || i}
                        onClick={() => handlePreview(u)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '0.7rem',
                          background: 'var(--cl-surface, #f8fafc)',
                          border: '1.5px solid var(--cl-border, #e2e8f0)',
                          borderRadius: 10,
                          padding: '0.7rem 1rem',
                          cursor: busyKey === u.key ? 'wait' : 'pointer',
                          transition: 'border-color 0.15s',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--cl-accent, #3b82f6)')}
                        onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--cl-border, #e2e8f0)')}
                      >
                        <span style={{ fontSize: '1.2rem', flexShrink: 0 }}>📎</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {u.name || 'Attached file'}
                          </p>
                          {u.size != null && (
                            <p style={{ margin: '2px 0 0', fontSize: '0.72rem', color: 'var(--cl-text-muted)' }}>{formatSize(u.size)}</p>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: '0.4rem', flexShrink: 0 }} onClick={e => e.stopPropagation()}>
                          <button
                            className="cl-btn cl-btn-secondary cl-btn-sm"
                            onClick={() => handleDownload(u)}
                            disabled={busyKey === u.key}
                          >
                            {busyKey === u.key ? '...' : 'Download'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Instructions-only: no study or uploads */}
              {isInstructionsOnly && (
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--cl-ok, #16a34a)', fontWeight: 600 }}>
                  ✓ Marked as read
                </p>
              )}
            </div>
          )}

          {/* ── Submission section (non-material only) ───────────────────── */}
          {!isMaterial && (
            <>
              <hr className="cl-divider" style={{ margin: 0 }} />

              <div>
                <p style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--cl-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 10px' }}>
                  My Submissions
                </p>

                {loadingSubs ? (
                  <div className="cl-skeleton" style={{ height: 36, borderRadius: 8 }} />
                ) : submissions.length === 0 ? (
                  <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--cl-text-secondary)' }}>
                    Not started yet.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {submissions.map((sub, i) => (
                      <div
                        key={sub.id || i}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '0.75rem',
                          background: 'var(--cl-bg)', borderRadius: 8, padding: '0.6rem 0.8rem',
                        }}
                      >
                        <span style={{ fontSize: '0.78rem', color: 'var(--cl-text-muted)', minWidth: 60 }}>
                          Attempt {sub.attempt}
                        </span>
                        <StatusBadge status={sub.status as any} />
                        {sub.score != null && (
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--cl-accent)' }}>
                            {Math.round(sub.score * 100)}%
                          </span>
                        )}
                        {sub.submitted_at && (
                          <span style={{ fontSize: '0.73rem', color: 'var(--cl-text-muted)', marginLeft: 'auto' }}>
                            {new Date(sub.submitted_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Overdue warning */}
              {isOverdue && !alreadySubmitted && (
                <div className="cl-error-banner">
                  This assignment is past due. Submitting now will be marked as late.
                </div>
              )}

              {/* Confirm submit */}
              {confirmed && canRetry && !alreadySubmitted && (
                <div style={{
                  background: 'var(--cl-accent-light)',
                  border: '1.5px solid #c7d2fe',
                  borderRadius: 10,
                  padding: '1rem 1.1rem',
                  display: 'flex', flexDirection: 'column', gap: '0.75rem',
                }}>
                  <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--cl-accent)', fontWeight: 600 }}>
                    Ready to submit?
                  </p>
                  <p style={{ margin: 0, fontSize: '0.83rem', color: 'var(--cl-text-secondary)' }}>
                    Once submitted, your attempt will be recorded. Your teacher will be able to see your submission.
                  </p>
                  {error && <div className="cl-error-banner">{error}</div>}
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={() => setConfirmed(false)}>Cancel</button>
                    <button className="cl-btn cl-btn-primary cl-btn-sm" onClick={handleSubmit} disabled={submitting}>
                      {submitting ? 'Submitting…' : 'Confirm Submit'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}

          {error && !confirmed && <div className="cl-error-banner">{error}</div>}
        </div>

        {/* Footer */}
        <div className="cl-modal__footer">
          <button className="cl-btn cl-btn-secondary" onClick={onClose}>Close</button>

          {/* Non-material: submit flow */}
          {!isMaterial && (
            <>
              {alreadySubmitted && !canRetry && (
                <span style={{ fontSize: '0.82rem', color: 'var(--cl-ok)', fontWeight: 600, alignSelf: 'center' }}>
                  ✓ Submitted
                </span>
              )}
              {(!alreadySubmitted || canRetry) && !confirmed && (
                <button
                  className="cl-btn cl-btn-primary"
                  onClick={() => {
                    if (!latestSub || latestSub.status === 'submitted') handleStartProgress();
                    setConfirmed(true);
                  }}
                  disabled={loadingSubs}
                >
                  {alreadySubmitted ? 'Retry Submission' : latestSub?.status === 'in_progress' ? 'Submit' : 'Start & Submit'}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
