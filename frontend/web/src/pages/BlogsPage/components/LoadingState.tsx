/**
 * Loading state component for blog content
 * Shows loading indicator while fetching data
 */

import React from 'react';

/**
 * Simple loading indicator with centered text
 */
const LoadingState: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        fontSize: '1.1rem',
        color: '#475569'
      }}
    >
      Loading articles...
    </div>
  );
};

export default LoadingState;
