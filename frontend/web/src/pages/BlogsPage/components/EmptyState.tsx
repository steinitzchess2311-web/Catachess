/**
 * Created at: 2026-07-09 01:27 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:27 EDT
 * Last Modified by: Codex
 *
 * Empty state component for blog content.
 */

import React from 'react';
import { FileTextIcon } from '@radix-ui/react-icons';

interface EmptyStateProps {
  message?: string;
}

/**
 * Empty state with customizable message
 */
const EmptyState: React.FC<EmptyStateProps> = ({ message = 'No articles found' }) => {
  return (
    <div className="blog-state">
      <div className="blog-state__icon">
        <FileTextIcon width={22} height={22} />
      </div>
      <p className="blog-state__title">
        {message}
      </p>
      <p className="blog-state__text">
        Try adjusting your search or filters
      </p>
    </div>
  );
};

export default EmptyState;
