/**
 * Created at: 2026-07-09 01:27 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:27 EDT
 * Last Modified by: Codex
 *
 * Pagination component for blog article lists.
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
  return (
    <div className="blog-pagination">
      <button
        className="blog-pagination__button"
        disabled={!pagination.has_prev}
        onClick={() => onPageChange(pagination.page - 1)}
      >
        Previous
      </button>

      <span className="blog-pagination__label">
        Page {pagination.page} of {pagination.total_pages}
      </span>

      <button
        className="blog-pagination__button"
        disabled={!pagination.has_next}
        onClick={() => onPageChange(pagination.page + 1)}
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;
