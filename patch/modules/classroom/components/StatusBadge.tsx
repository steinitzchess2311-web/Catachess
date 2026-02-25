import React from 'react';
import type { SubmissionStatus } from '../types';

interface Props { status: SubmissionStatus; }

const LABELS: Record<SubmissionStatus, string> = {
  submitted:   'Submitted',
  in_progress: 'In Progress',
  not_started: 'Not Started',
  overdue:     'Overdue',
};

export const StatusBadge: React.FC<Props> = ({ status }) => (
  <span className={`cl-status-badge cl-status-badge--${status}`}>
    {LABELS[status]}
  </span>
);
