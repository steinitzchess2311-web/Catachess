/**
 * Created at: 2026-07-09 01:27 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:27 EDT
 * Last Modified by: Codex
 *
 * Error state component for blog content.
 */

import React from 'react';
import { ExclamationTriangleIcon } from '@radix-ui/react-icons';

interface ErrorStateProps {
  message?: string;
}

/**
 * Error state with customizable message
 */
const ErrorState: React.FC<ErrorStateProps> = ({ message = 'Failed to load articles' }) => {
  return (
    <div className="blog-state blog-state--error">
      <div className="blog-state__icon">
        <ExclamationTriangleIcon width={22} height={22} />
      </div>
      <p className="blog-state__title">
        {message}
      </p>
      <p className="blog-state__text">
        Please try again later
      </p>
    </div>
  );
};

export default ErrorState;
