import React from 'react';
import type { AssignmentCategory } from '../types';

interface Props { category: AssignmentCategory; }

const LABELS: Record<AssignmentCategory, string> = {
  material: 'Material',
  assignment: 'Assignment',
  exam: 'Exam',
};

export const CategoryBadge: React.FC<Props> = ({ category }) => (
  <span className={`cl-cat-badge cl-cat-badge--${category}`}>
    {LABELS[category]}
  </span>
);
