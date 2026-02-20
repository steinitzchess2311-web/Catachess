import React from 'react';
import type { MastersFilters } from '../types';

interface FilterBarProps {
  filters: MastersFilters;
  onChange: (f: MastersFilters) => void;
}

export function FilterBar({ filters, onChange }: FilterBarProps) {
  return (
    <div className="explorer-filters">
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
    </div>
  );
}
