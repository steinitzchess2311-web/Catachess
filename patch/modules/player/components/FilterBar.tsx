// ============================================================
// FilterBar — color, outcome, score, year, sort filters
// ============================================================

import React from 'react';
import type { SearchFilters, ColorFilter, PlayerResult, ColorResult, SortOrder } from '../types';

interface Props {
  filters: SearchFilters;
  onChange: (f: SearchFilters) => void;
}

const COLOR_OPTS: { value: ColorFilter; label: string }[] = [
  { value: 'any',   label: 'Any' },
  { value: 'white', label: 'White' },
  { value: 'black', label: 'Black' },
];

// Player-perspective: did the player win/lose/draw?
const OUTCOME_OPTS: { value: PlayerResult | ''; label: string }[] = [
  { value: '',      label: 'Any' },
  { value: 'win',   label: 'Win' },
  { value: 'loss',  label: 'Loss' },
  { value: 'draw',  label: 'Draw' },
];

// Color-perspective: which side won on the board?
const SCORE_OPTS: { value: ColorResult | ''; label: string }[] = [
  { value: '',       label: 'Any' },
  { value: 'white',  label: '1–0' },
  { value: 'black',  label: '0–1' },
  { value: 'draw',   label: '½–½' },
];

const SORT_OPTS: { value: SortOrder; label: string }[] = [
  { value: 'elo_desc',  label: 'Elo ↓' },
  { value: 'year_desc', label: 'Newest' },
  { value: 'year_asc',  label: 'Oldest' },
];

export function FilterBar({ filters, onChange }: Props) {
  function set<K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="ps-filter-bar">
      {/* Color chips */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">Color</span>
        <div className="ps-chips">
          {COLOR_OPTS.map(o => (
            <button
              key={o.value}
              className={`ps-chip${filters.color === o.value ? ' is-active' : ''}`}
              onClick={() => set('color', o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {/* Outcome chips — player perspective (Win / Loss / Draw) */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">Outcome</span>
        <div className="ps-chips">
          {OUTCOME_OPTS.map(o => (
            <button
              key={o.value}
              className={`ps-chip${filters.playerResult === o.value ? ' is-active' : ''}`}
              onClick={() => set('playerResult', o.value as SearchFilters['playerResult'])}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {/* Score chips — color perspective (1–0 / 0–1 / ½–½) */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">Score</span>
        <div className="ps-chips">
          {SCORE_OPTS.map(o => (
            <button
              key={o.value}
              className={`ps-chip${filters.colorResult === o.value ? ' is-active' : ''}`}
              onClick={() => set('colorResult', o.value as SearchFilters['colorResult'])}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {/* Year range */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">Year</span>
        <div className="ps-filter-years">
          <input
            type="number"
            className="ps-year-input"
            placeholder="From"
            min={1900}
            max={2030}
            value={filters.yearFrom}
            onChange={e => set('yearFrom', e.target.value)}
          />
          <span className="ps-year-sep">—</span>
          <input
            type="number"
            className="ps-year-input"
            placeholder="To"
            min={1900}
            max={2030}
            value={filters.yearTo}
            onChange={e => set('yearTo', e.target.value)}
          />
        </div>
      </div>

      {/* Sort */}
      <div className="ps-filter-group ps-filter-group--sort">
        <span className="ps-filter-label">Sort</span>
        <div className="ps-chips">
          {SORT_OPTS.map(o => (
            <button
              key={o.value}
              className={`ps-chip${filters.sort === o.value ? ' is-active' : ''}`}
              onClick={() => set('sort', o.value)}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
