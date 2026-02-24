/**
 * Pagination component for blog article lists
 * Provides Previous/Next navigation with page info
 */

import React from 'react';

interface PaginationProps {
  pagination: {
    page: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  onPageChange: (page: number) => void;
}

/**
 * Pagination controls with disabled states
 */
const Pagination: React.FC<PaginationProps> = ({ pagination, onPageChange }) => {
  const buttonStyle = {
    padding: '10px 20px',
    fontSize: '0.95rem',
    fontWeight: 500,
    color: '#0f172a',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  };

  const disabledStyle = {
    ...buttonStyle,
    opacity: 0.5,
    cursor: 'not-allowed'
  };

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
        marginTop: '40px',
        padding: '20px'
      }}
    >
      <button
        style={pagination.has_prev ? buttonStyle : disabledStyle}
        disabled={!pagination.has_prev}
        onClick={() => onPageChange(pagination.page - 1)}
        onMouseEnter={(e) => {
          if (pagination.has_prev) {
            e.currentTarget.style.backgroundColor = 'rgba(139, 115, 85, 0.1)';
            e.currentTarget.style.borderColor = '#2563eb';
          }
        }}
        onMouseLeave={(e) => {
          if (pagination.has_prev) {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            e.currentTarget.style.borderColor = '#e0e0e0';
          }
        }}
      >
        Previous
      </button>

      <span
        style={{
          fontSize: '0.95rem',
          color: '#475569',
          fontWeight: 500
        }}
      >
        Page {pagination.page} of {pagination.total_pages}
      </span>

      <button
        style={pagination.has_next ? buttonStyle : disabledStyle}
        disabled={!pagination.has_next}
        onClick={() => onPageChange(pagination.page + 1)}
        onMouseEnter={(e) => {
          if (pagination.has_next) {
            e.currentTarget.style.backgroundColor = 'rgba(139, 115, 85, 0.1)';
            e.currentTarget.style.borderColor = '#2563eb';
          }
        }}
        onMouseLeave={(e) => {
          if (pagination.has_next) {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            e.currentTarget.style.borderColor = '#e0e0e0';
          }
        }}
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;
