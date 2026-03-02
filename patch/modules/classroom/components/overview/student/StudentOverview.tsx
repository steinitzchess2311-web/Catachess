import React, { useEffect, useMemo, useRef, useState } from 'react';
import { getMyTodo, getAssignment } from '../../../api';
import type { Classroom, TodoItem, Assignment } from '../../../types';
import { WorkspaceShareModal } from '../../WorkspaceShareModal';
import { AssignmentDetailModal } from '../../AssignmentDetailModal';
import { StatusBadge } from '../../StatusBadge';
import { CategoryBadge } from '../../CategoryBadge';
import { BroadcastBanner } from '../../BroadcastBanner';
import { formatDue, dueCssModifier } from '../../../utils';

interface StudentOverviewProps {
  classroom: Classroom;
  focusTasksSignal?: number;
}

export const StudentOverview: React.FC<StudentOverviewProps> = ({ classroom, focusTasksSignal = 0 }) => {
  const [todo, setTodo] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareSuccessMsg, setShareSuccessMsg] = useState<string | null>(null);
  const [detailTarget, setDetailTarget] = useState<Assignment | null>(null);
  const [loadingDetail, setLoadingDetail] = useState<string | null>(null);
  const tasksRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    getMyTodo()
      .then(all =>
        setTodo(
          all.filter(t =>
            !t.classroom_id
              ? t.classroom_name === classroom.name
              : t.classroom_id === classroom.id,
          ),
        ),
      )
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id, classroom.name]);

  useEffect(() => {
    if (!focusTasksSignal || !tasksRef.current) return;
    tasksRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [focusTasksSignal]);

  async function handleOpenTask(item: TodoItem) {
    if (loadingDetail) return;
    setLoadingDetail(item.assignment_id);
    try {
      const full = await getAssignment(classroom.id, item.assignment_id);
      setDetailTarget(full);
    } catch {
      // ignore
    } finally {
      setLoadingDetail(null);
    }
  }

  const overdueCount = useMemo(() => todo.filter(t => t.urgency === 'overdue').length, [todo]);
  const dueSoonCount = useMemo(() => todo.filter(t => t.urgency === 'due_soon').length, [todo]);
  const doneCount = useMemo(() => todo.filter(t => t.my_status === 'submitted').length, [todo]);

  return (
    <div className="cl-overview-stack">
      <BroadcastBanner classroomId={classroom.id} />

      <div className="cl-overview-stats cl-overview-stats--calm">
        <div className="cl-ov-stat cl-ov-stat--accent-soft">
          <span className="cl-ov-stat__val">{overdueCount}</span>
          <span className="cl-ov-stat__lbl">Overdue</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--accent-soft">
          <span className="cl-ov-stat__val">{dueSoonCount}</span>
          <span className="cl-ov-stat__lbl">Due Soon</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--accent">
          <span className="cl-ov-stat__val">{doneCount}</span>
          <span className="cl-ov-stat__lbl">Completed</span>
        </div>
      </div>

      <section className="cl-panel" ref={tasksRef}>
        <div className="cl-section-header cl-section-header--compact">
          <h3 className="cl-section-title">My Tasks</h3>
          <button
            className="cl-btn cl-btn-secondary cl-btn-sm"
            onClick={() => {
              setShareSuccessMsg(null);
              setShowShareModal(true);
            }}
          >
            Share to Teacher
          </button>
        </div>

        {shareSuccessMsg && <p className="cl-inline-success">{shareSuccessMsg}</p>}

        {loading ? (
          <div className="cl-stack-sm">
            {[...Array(3)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 56, borderRadius: 10 }} />)}
          </div>
        ) : todo.length === 0 ? (
          <div className="cl-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p className="cl-empty__title">All caught up!</p>
            <p className="cl-empty__sub">No pending tasks in this class.</p>
          </div>
        ) : (
          <div className="cl-asgn-list">
            {todo.map(item => {
              const dueModifier = item.due_date ? dueCssModifier(item.due_date) : 'normal';
              const isOverdue = item.due_date ? new Date(item.due_date) < new Date() : false;
              return (
                <div
                  key={item.assignment_id}
                  className="cl-asgn-card"
                  onClick={() => handleOpenTask(item)}
                  style={{ cursor: 'pointer' }}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => e.key === 'Enter' && handleOpenTask(item)}
                >
                  <div className="cl-asgn-card__left">
                    <span className="cl-asgn-card__title">{item.title}</span>
                    <div className="cl-asgn-card__sub">
                      <CategoryBadge category={item.category} />
                      {item.due_date ? (
                        <span className={`cl-asgn-card__due cl-asgn-card__due--${dueModifier}`}>
                          {isOverdue ? 'Was due' : 'Due'} {formatDue(item.due_date)}
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted)' }}>No due date</span>
                      )}
                    </div>
                  </div>
                  <div className="cl-asgn-card__right">
                    {loadingDetail === item.assignment_id ? (
                      <span className="cl-status-badge">Loading…</span>
                    ) : (
                      <StatusBadge status={item.my_status as any} />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {detailTarget && (
        <AssignmentDetailModal
          classroomId={classroom.id}
          assignment={detailTarget}
          onClose={() => setDetailTarget(null)}
          onSubmitted={() => {
            setDetailTarget(null);
            // Refresh todo list
            getMyTodo()
              .then(all =>
                setTodo(
                  all.filter(t =>
                    !t.classroom_id
                      ? t.classroom_name === classroom.name
                      : t.classroom_id === classroom.id,
                  ),
                ),
              )
              .catch(() => {});
          }}
        />
      )}

      {showShareModal && (
        <WorkspaceShareModal
          classroomId={classroom.id}
          onClose={() => setShowShareModal(false)}
          onShared={title => {
            setShowShareModal(false);
            setShareSuccessMsg(`\"${title}\" shared with teacher`);
            setTimeout(() => setShareSuccessMsg(null), 4000);
          }}
        />
      )}
    </div>
  );
};
