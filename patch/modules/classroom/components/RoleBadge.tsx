import React from 'react';
import type { ClassroomRole } from '../types';

interface Props { role: ClassroomRole; }

const LABELS: Record<ClassroomRole, string> = {
  owner: 'Owner',
  teacher: 'Teacher',
  student: 'Student',
};

export const RoleBadge: React.FC<Props> = ({ role }) => (
  <span className={`cl-role-badge cl-role-badge--${role}`}>
    {LABELS[role]}
  </span>
);
