/**
 * Empty state component for blog content
 * Shows when no articles match the current filters
 */

import React from 'react';

interface EmptyStateProps {
  message?: string;
}

/**
 * Empty state with customizable message
 */
const EmptyState: React.FC<EmptyStateProps> = ({ message = 'No articles found' }) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px',
        padding: '40px',
        textAlign: 'center'
      }}
    >
      <div
        style={{
          fontSize: '3rem',
          marginBottom: '16px',
          opacity: 0.3
        }}
      >
        📝
      </div>
      <p
        style={{
          fontSize: '1.1rem',
          color: '#475569',
          margin: 0
        }}
      >
        {message}
      </p>
      <p
        style={{
          fontSize: '0.95rem',
          color: '#8a8a8a',
          marginTop: '8px'
        }}
      >
        Try adjusting your search or filters
      </p>
    </div>
  );
};

export default EmptyState;
