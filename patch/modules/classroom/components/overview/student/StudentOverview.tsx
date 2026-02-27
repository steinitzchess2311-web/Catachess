import React, { useEffect, useMemo, useRef, useState } from 'react';
import { getMyTodo } from '../../../api';
import type { Classroom, TodoItem } from '../../../types';
import { WorkspaceShareModal } from '../../WorkspaceShareModal';
import { StatusBadge } from '../../StatusBadge';
import { BroadcastBanner } from '../../BroadcastBanner';
import { formatDue } from '../../../utils';

interface StudentOverviewProps {
  classroom: Classroom;
  focusTasksSignal?: number;
}

export const StudentOverview: React.FC<StudentOverviewProps> = ({ classroom, focusTasksSignal = 0 }) => {
  const [todo, setTodo] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareSuccessMsg, setShareSuccessMsg] = useState<string | null>(null);
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
          <div className="cl-todo-list">
            {todo.map(item => (
              <div key={item.assignment_id} className={`cl-todo-item cl-todo-item--${item.urgency}`}>
                <div className={`cl-urgency-dot cl-urgency-dot--${item.urgency}`} />
                <div className="cl-todo-item__body">
                  <p className="cl-todo-item__title">{item.title}</p>
                  <p className="cl-todo-item__sub">
                    {item.due_date ? `Due ${formatDue(item.due_date)}` : 'No due date'}
                  </p>
                </div>
                <StatusBadge status={item.my_status as any} />
              </div>
            ))}
          </div>
        )}
      </section>

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
