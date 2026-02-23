import React from 'react';
import type { MastersFilters } from '../types';

interface FilterBarProps {
  filters: MastersFilters;
  onChange: (f: MastersFilters) => void;
  /** When true, year filters are visually paused (player filter is active) */
  playerFilterActive?: boolean;
}

export function FilterBar({ filters, onChange, playerFilterActive }: FilterBarProps) {
  return (
    <div className={`explorer-filters${playerFilterActive ? ' explorer-filters--paused' : ''}`}>
      <div className="explorer-filter-row">
        <span className="explorer-filter-label">Since</span>
        <input
          type="number"
          className="explorer-year-input"
          placeholder="1995"
          min={1995}
          max={2030}
          value={filters.since ?? ''}
          onChange={(e) =>
            onChange({ ...filters, since: e.target.value ? Number(e.target.value) : undefined })
          }
        />
        <span className="explorer-filter-label">Until</span>
        <input
          type="number"
          className="explorer-year-input"
          placeholder="2026"
          min={1995}
          max={2030}
          value={filters.until ?? ''}
          onChange={(e) =>
            onChange({ ...filters, until: e.target.value ? Number(e.target.value) : undefined })
          }
        />
      </div>

      {playerFilterActive && (
        <div className="explorer-filter-paused-note">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          Year filters paused — player filter active
        </div>
      )}
    </div>
  );
}
