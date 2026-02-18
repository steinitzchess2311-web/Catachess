import React from 'react';
import type {
  ExplorerTab,
  MastersFilters,
  LichessFilters,
  PlayerFilters,
  SpeedType,
  RatingValue,
} from '../types';
import { SPEED_LABELS, RATING_VALUES } from '../types';

// ---- helpers -----------------------------------------------

function toggle<T>(arr: T[], item: T): T[] {
  return arr.includes(item) ? arr.filter((x) => x !== item) : [...arr, item];
}

// ---- Masters -----------------------------------------------

function MastersFilter({
  filters,
  onChange,
}: {
  filters: MastersFilters;
  onChange: (f: MastersFilters) => void;
}) {
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

// ---- Speed chips -------------------------------------------

const SPEEDS: SpeedType[] = ['ultraBullet', 'bullet', 'blitz', 'rapid', 'classical', 'correspondence'];

function SpeedPicker({
  selected,
  onChange,
}: {
  selected: SpeedType[];
  onChange: (s: SpeedType[]) => void;
}) {
  return (
    <div className="explorer-filter-row">
      <span className="explorer-filter-label">Time</span>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {SPEEDS.map((s) => (
          <button
            key={s}
            type="button"
            className={`explorer-chip${selected.includes(s) ? ' is-active' : ''}`}
            onClick={() => onChange(toggle(selected, s))}
          >
            {SPEED_LABELS[s]}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---- Rating chips ------------------------------------------

function RatingPicker({
  selected,
  onChange,
}: {
  selected: RatingValue[];
  onChange: (r: RatingValue[]) => void;
}) {
  return (
    <div className="explorer-filter-row">
      <span className="explorer-filter-label">Elo</span>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {RATING_VALUES.map((r) => (
          <button
            key={r}
            type="button"
            className={`explorer-chip${selected.includes(r) ? ' is-active' : ''}`}
            onClick={() => onChange(toggle(selected as RatingValue[], r))}
          >
            {r === 0 ? '–1k' : `${r / 1000}k+`}
          </button>
        ))}
      </div>
    </div>
  );
}

// ---- Lichess -----------------------------------------------

function LichessFilter({
  filters,
  onChange,
}: {
  filters: LichessFilters;
  onChange: (f: LichessFilters) => void;
}) {
  return (
    <div className="explorer-filters">
      <SpeedPicker
        selected={filters.speeds}
        onChange={(speeds) => onChange({ ...filters, speeds })}
      />
      <RatingPicker
        selected={filters.ratings}
        onChange={(ratings) => onChange({ ...filters, ratings })}
      />
    </div>
  );
}

// ---- Player ------------------------------------------------

function PlayerFilter({
  filters,
  onChange,
  onSearch,
}: {
  filters: PlayerFilters;
  onChange: (f: PlayerFilters) => void;
  onSearch: () => void;
}) {
  return (
    <div className="explorer-filters">
      <div className="explorer-player-row">
        <input
          type="text"
          className="explorer-player-input"
          placeholder="Lichess username"
          value={filters.player}
          onChange={(e) => onChange({ ...filters, player: e.target.value })}
          onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        />
        <button
          type="button"
          className={`explorer-chip${filters.color === 'white' ? ' is-active' : ''}`}
          onClick={() => onChange({ ...filters, color: 'white' })}
        >
          White
        </button>
        <button
          type="button"
          className={`explorer-chip${filters.color === 'black' ? ' is-active' : ''}`}
          onClick={() => onChange({ ...filters, color: 'black' })}
        >
          Black
        </button>
      </div>
      <SpeedPicker
        selected={filters.speeds}
        onChange={(speeds) => onChange({ ...filters, speeds })}
      />
      <div className="explorer-filter-row" style={{ justifyContent: 'flex-end' }}>
        <button type="button" className="explorer-search-btn" onClick={onSearch}>
          Search
        </button>
      </div>
    </div>
  );
}

// ---- Public ------------------------------------------------

interface FilterBarProps {
  tab: ExplorerTab;
  mastersFilters: MastersFilters;
  setMastersFilters: (f: MastersFilters) => void;
  lichessFilters: LichessFilters;
  setLichessFilters: (f: LichessFilters) => void;
  playerFilters: PlayerFilters;
  setPlayerFilters: (f: PlayerFilters) => void;
  onPlayerSearch: () => void;
}

export function FilterBar({
  tab,
  mastersFilters,
  setMastersFilters,
  lichessFilters,
  setLichessFilters,
  playerFilters,
  setPlayerFilters,
  onPlayerSearch,
}: FilterBarProps) {
  if (tab === 'masters') {
    return <MastersFilter filters={mastersFilters} onChange={setMastersFilters} />;
  }
  if (tab === 'lichess') {
    return <LichessFilter filters={lichessFilters} onChange={setLichessFilters} />;
  }
  return (
    <PlayerFilter
      filters={playerFilters}
      onChange={setPlayerFilters}
      onSearch={onPlayerSearch}
    />
  );
}
