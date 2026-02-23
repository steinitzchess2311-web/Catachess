// ============================================================
// FilterBar — 颜色、结果、年份、排序过滤器
// ============================================================

import React from 'react';
import type { SearchFilters, ColorFilter, ResultFilter, SortOrder } from '../types';

interface Props {
  filters: SearchFilters;
  onChange: (f: SearchFilters) => void;
}

const COLOR_OPTS: { value: ColorFilter; label: string }[] = [
  { value: 'any',   label: '不限颜色' },
  { value: 'white', label: '执白' },
  { value: 'black', label: '执黑' },
];

const RESULT_OPTS: { value: ResultFilter | ''; label: string }[] = [
  { value: '',      label: '不限结果' },
  { value: 'white', label: '白胜' },
  { value: 'black', label: '黑胜' },
  { value: 'draw',  label: '平局' },
];

const SORT_OPTS: { value: SortOrder; label: string }[] = [
  { value: 'elo_desc',  label: 'Elo 高→低' },
  { value: 'year_desc', label: '最新优先' },
  { value: 'year_asc',  label: '最早优先' },
];

export function FilterBar({ filters, onChange }: Props) {
  function set<K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) {
    onChange({ ...filters, [key]: value });
  }

  return (
    <div className="ps-filter-bar">
      {/* 颜色 chips */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">颜色</span>
        <div className="ps-chips">
          {COLOR_OPTS.map((o) => (
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

      {/* 结果 chips */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">结果</span>
        <div className="ps-chips">
          {RESULT_OPTS.map((o) => (
            <button
              key={o.value}
              className={`ps-chip${filters.result === o.value ? ' is-active' : ''}`}
              onClick={() => set('result', o.value as SearchFilters['result'])}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>

      {/* 年份范围 */}
      <div className="ps-filter-group">
        <span className="ps-filter-label">年份</span>
        <div className="ps-filter-years">
          <input
            type="number"
            className="ps-year-input"
            placeholder="从"
            min={1900}
            max={2030}
            value={filters.yearFrom}
            onChange={(e) => set('yearFrom', e.target.value)}
          />
          <span className="ps-year-sep">—</span>
          <input
            type="number"
            className="ps-year-input"
            placeholder="至"
            min={1900}
            max={2030}
            value={filters.yearTo}
            onChange={(e) => set('yearTo', e.target.value)}
          />
        </div>
      </div>

      {/* 排序 */}
      <div className="ps-filter-group ps-filter-group--sort">
        <span className="ps-filter-label">排序</span>
        <div className="ps-chips">
          {SORT_OPTS.map((o) => (
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
