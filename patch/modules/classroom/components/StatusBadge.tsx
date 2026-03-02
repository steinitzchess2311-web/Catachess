import React from 'react';
import type { SubmissionStatus } from '../types';

interface Props { status: SubmissionStatus; isMaterial?: boolean; }

const LABELS: Record<SubmissionStatus, string> = {
  submitted:   'Submitted',
  in_progress: 'In Progress',
  not_started: 'Not Started',
  overdue:     'Overdue',
};

const MATERIAL_LABELS: Record<SubmissionStatus, string> = {
  submitted:   'Finished',
  in_progress: 'In Progress',
  not_started: 'Not Started',
  overdue:     'Overdue',
};

export const StatusBadge: React.FC<Props> = ({ status, isMaterial }) => (
  <span className={`cl-status-badge cl-status-badge--${status}`}>
    {(isMaterial ? MATERIAL_LABELS : LABELS)[status]}
  </span>
);
