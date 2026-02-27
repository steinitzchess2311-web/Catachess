import React, { useEffect, useState } from 'react';
import { listAssignments } from '../../../api';
import type { Assignment, Classroom } from '../../../types';
import { CategoryBadge } from '../../CategoryBadge';
import { ActivityFeed } from '../../ActivityFeed';
import { BroadcastPanel } from '../../BroadcastPanel';
import { formatDue } from '../../../utils';

interface TeacherOverviewProps {
  classroom: Classroom;
  broadcastRefreshKey?: number;
}

export const TeacherOverview: React.FC<TeacherOverviewProps> = ({ classroom, broadcastRefreshKey }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAssignments(classroom.id)
      .then(data => setAssignments(data.slice(0, 5)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id]);

  const memberCount = classroom.member_count ?? 0;
  const totalSubmitted = assignments.reduce((s, a) => s + (a.submission_count ?? 0), 0);

  return (
    <div className="cl-overview-stack">
      <div className="cl-overview-stats cl-overview-stats--calm">
        <div className="cl-ov-stat cl-ov-stat--accent">
          <span className="cl-ov-stat__val">{memberCount}</span>
          <span className="cl-ov-stat__lbl">Members</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--accent-soft">
          <span className="cl-ov-stat__val">{assignments.length}</span>
          <span className="cl-ov-stat__lbl">Assignments</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--accent-soft">
          <span className="cl-ov-stat__val">{totalSubmitted}</span>
          <span className="cl-ov-stat__lbl">Submissions</span>
        </div>
      </div>

      <div className="cl-overview-layout">
        <section className="cl-panel">
          <div className="cl-section-header cl-section-header--compact">
            <h3 className="cl-section-title">Recent Assignments</h3>
          </div>
          {loading ? (
            <div className="cl-stack-sm">
              {[...Array(3)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 56, borderRadius: 10 }} />)}
            </div>
          ) : assignments.length === 0 ? (
            <div className="cl-panel-empty">
              <p className="cl-panel-empty__title">No assignments yet</p>
              <p className="cl-panel-empty__sub">Use Create Assignment to publish the first task.</p>
            </div>
          ) : (
            <div className="cl-stack-sm">
              {assignments.map(a => (
                <article key={a.id} className="cl-mini-card">
                  <div className="cl-mini-card__top">
                    <CategoryBadge category={a.category} />
                    <span className="cl-mini-card__title">{a.title}</span>
                  </div>
                  <div className="cl-mini-card__meta">
                    <span>{a.due_date ? `Due ${formatDue(a.due_date)}` : 'No due date'}</span>
                    <span>{a.submission_count ?? 0}/{a.member_count ?? '—'}</span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <aside className="cl-overview-side-stack">
          <section className="cl-panel">
            <BroadcastPanel classroomId={classroom.id} refreshKey={broadcastRefreshKey} />
          </section>
          <section className="cl-panel">
            <div className="cl-section-header cl-section-header--compact">
              <h3 className="cl-section-title">Recent Activity</h3>
            </div>
            <ActivityFeed classroomId={classroom.id} />
          </section>
        </aside>
      </div>
    </div>
  );
};
