/**
 * Created at: 2026-07-09 01:27 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:27 EDT
 * Last Modified by: Codex
 *
 * Loading state component for blog content.
 */

import React from 'react';

/**
 * Simple loading indicator with centered text
 */
const LoadingState: React.FC = () => {
  return (
    <div className="blog-state">
      <div className="blog-state__spinner" />
      <p className="blog-state__title">Loading articles...</p>
    </div>
  );
};

export default LoadingState;
