import React, { useEffect, useState } from 'react';
import { listAssignments, deleteAssignment } from '../api';
import type { Classroom, Assignment, AssignmentCategory } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { StatusBadge } from './StatusBadge';
import { CreateAssignmentModal } from './CreateAssignmentModal';
import { StatsModal } from './StatsModal';
import { formatDue, dueCssModifier } from '../utils';

const CATEGORY_FILTERS: { label: string; value: AssignmentCategory | 'all' }[] = [
  { label: 'All', value: 'all' },
  { label: 'Material', value: 'material' },
  { label: 'Assignment', value: 'assignment' },
  { label: 'Exam', value: 'exam' },
];

interface Props {
  classroom: Classroom;
}

export const AssignmentsTab: React.FC<Props> = ({ classroom }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterCategory, setFilterCategory] = useState<AssignmentCategory | 'all'>('all');
  const [showCreate, setShowCreate] = useState(false);
  const [statsTarget, setStatsTarget] = useState<Assignment | null>(null);

  const isTeacher = classroom.my_role === 'owner' || classroom.my_role === 'teacher';

  useEffect(() => {
    setLoading(true);
    const params = filterCategory !== 'all' ? { category: filterCategory } : undefined;
    listAssignments(classroom.id, params)
      .then(setAssignments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id, filterCategory]);

  async function handleDelete(id: string, title: string) {
    if (!confirm(`Retract assignment "${title}"? This cannot be undone.`)) return;
    try {
      await deleteAssignment(classroom.id, id);
      setAssignments(prev => prev.filter(a => a.id !== id));
    } catch (err: any) {
      alert(err?.message || 'Failed to delete assignment.');
    }
  }

  return (
    <div>
      <div className="cl-section-header" style={{ marginBottom: '1rem' }}>
        {/* Category filter */}
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          {CATEGORY_FILTERS.map(f => (
            <button
              key={f.value}
              className={`cl-btn cl-btn-sm ${filterCategory === f.value ? 'cl-btn-primary' : 'cl-btn-secondary'}`}
              onClick={() => setFilterCategory(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
        {isTeacher && (
          <button className="cl-btn cl-btn-primary cl-btn-sm" onClick={() => setShowCreate(true)}>
            + New Assignment
          </button>
        )}
      </div>

      {loading ? (
        <div className="cl-asgn-list">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 64, borderRadius: 10 }} />
          ))}
        </div>
      ) : assignments.length === 0 ? (
        <div className="cl-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          <p className="cl-empty__title">No assignments yet</p>
          {isTeacher && <p className="cl-empty__sub">Click "+ New Assignment" to publish a task.</p>}
        </div>
      ) : (
        <div className="cl-asgn-list">
          {assignments.map(a => (
            <div key={a.id} className="cl-asgn-card">
              <div className="cl-asgn-card__left">
                <span className="cl-asgn-card__title">{a.title}</span>
                <div className="cl-asgn-card__sub">
                  <CategoryBadge category={a.category} />
                  <span style={{ fontSize: '0.78rem', color: 'var(--cl-text-muted)', textTransform: 'capitalize' }}>
                    {a.type}
                  </span>
                  {a.due_date && (
                    <span className={`cl-asgn-card__due cl-asgn-card__due--${dueCssModifier(a.due_date)}`}>
                      Due {formatDue(a.due_date)}
                    </span>
                  )}
                </div>
              </div>
              <div className="cl-asgn-card__right">
                {/* Teacher view */}
                {isTeacher && a.submission_count !== undefined && (
                  <span className="cl-asgn-card__progress">
                    {a.submission_count} / {a.member_count ?? '—'}
                  </span>
                )}
                {/* Student view */}
                {!isTeacher && a.my_submission && (
                  <StatusBadge status={a.my_submission.status} />
                )}
                {isTeacher && (
                  <button
                    className="cl-btn-icon"
                    title="View stats"
                    onClick={() => setStatsTarget(a)}
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
                    </svg>
                  </button>
                )}
                {isTeacher && (
                  <button
                    className="cl-btn-icon"
                    title="Retract"
                    onClick={() => handleDelete(a.id, a.title)}
                    style={{ color: 'var(--cl-text-muted)' }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                      <path d="M10 11v6M14 11v6"/>
                    </svg>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showCreate && (
        <CreateAssignmentModal
          classroomId={classroom.id}
          onClose={() => setShowCreate(false)}
          onCreated={a => {
            setAssignments(prev => [a, ...prev]);
            setShowCreate(false);
          }}
        />
      )}

      {statsTarget && (
        <StatsModal
          classroomId={classroom.id}
          assignment={statsTarget}
          onClose={() => setStatsTarget(null)}
        />
      )}
    </div>
  );
};
