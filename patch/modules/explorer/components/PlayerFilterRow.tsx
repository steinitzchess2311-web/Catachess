// ============================================================
// PlayerFilterRow — in-panel player filter for Explorer
//
// • Empty state  : "Filter by player..." trigger (dashed)
// • Active state : selected player badges + "Add spelling" button
// • Autocomplete : portal dropdown via /search/players
// ============================================================

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { fetchPlayerSuggestions } from '../api';
import type { PlayerSuggestion } from '../api';

interface Props {
  players: string[];
  onAdd: (name: string) => void;
  onRemove: (name: string) => void;
}

function formatGames(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}

// ---- Autocomplete dropdown (portaled to body) ---------------

interface DropdownProps {
  suggestions: PlayerSuggestion[];
  loading: boolean;
  query: string;
  anchor: DOMRect;
  onSelect: (name: string) => void;
}

function Dropdown({ suggestions, loading, query, anchor, onSelect }: DropdownProps) {
  return createPortal(
    <ul
      className="explorer-pf-dropdown"
      style={{
        position: 'fixed',
        top: anchor.bottom + 4,
        left: anchor.left,
        width: Math.max(anchor.width, 200),
        zIndex: 1200,
      }}
      // Prevent document mousedown from firing (click-outside handler)
      onMouseDown={e => e.stopPropagation()}
    >
      {loading && (
        <li className="explorer-pf-dropdown__state">
          <span className="explorer-pf-spin" aria-hidden />
          Searching…
        </li>
      )}
      {!loading && query.length >= 2 && suggestions.length === 0 && (
        <li className="explorer-pf-dropdown__state explorer-pf-dropdown__state--empty">
          No players found
        </li>
      )}
      {suggestions.map(s => (
        <li
          key={s.name}
          className="explorer-pf-dropdown__item"
          // mousedown to fire before blur; preventDefault keeps input focused
          onMouseDown={e => { e.preventDefault(); onSelect(s.name); }}
        >
          <span className="explorer-pf-dropdown__name">{s.name}</span>
          <span className="explorer-pf-dropdown__games">{formatGames(s.games)}</span>
        </li>
      ))}
    </ul>,
    document.body,
  );
}

// ---- Main component -----------------------------------------

export function PlayerFilterRow({ players, onAdd, onRemove }: Props) {
  const [open,        setOpen]        = useState(false);
  const [query,       setQuery]       = useState('');
  const [suggestions, setSuggestions] = useState<PlayerSuggestion[]>([]);
  const [loading,     setLoading]     = useState(false);
  const [anchor,      setAnchor]      = useState<DOMRect | null>(null);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const wrapRef  = useRef<HTMLDivElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const updateAnchor = useCallback(() => {
    if (wrapRef.current) setAnchor(wrapRef.current.getBoundingClientRect());
  }, []);

  // Open: focus input + measure anchor
  useEffect(() => {
    if (open) {
      updateAnchor();
      requestAnimationFrame(() => inputRef.current?.focus());
    } else {
      setQuery('');
      setSuggestions([]);
      setLoading(false);
      if (timerRef.current) clearTimeout(timerRef.current);
      abortRef.current?.abort();
    }
  }, [open, updateAnchor]);

  // Re-anchor on scroll / resize while open
  useEffect(() => {
    if (!open) return;
    window.addEventListener('scroll', updateAnchor, true);
    window.addEventListener('resize', updateAnchor);
    return () => {
      window.removeEventListener('scroll', updateAnchor, true);
      window.removeEventListener('resize', updateAnchor);
    };
  }, [open, updateAnchor]);

  // Click outside → close
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  // Debounced autocomplete fetch
  const handleChange = useCallback((val: string) => {
    setQuery(val);
    if (timerRef.current) clearTimeout(timerRef.current);
    abortRef.current?.abort();

    if (val.length < 2) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    timerRef.current = setTimeout(() => {
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      fetchPlayerSuggestions(val, 8, ctrl.signal)
        .then(data => {
          // Filter out already-selected players
          setSuggestions(data.players.filter(p => !players.includes(p.name)));
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }, 200);
  }, [players]);

  const handleSelect = useCallback((name: string) => {
    onAdd(name);
    setQuery('');
    setSuggestions([]);
    setLoading(false);
    // Stay open to add more spelling variants
    requestAnimationFrame(() => inputRef.current?.focus());
  }, [onAdd]);

  const showDropdown = open && anchor !== null && (loading || suggestions.length > 0 || query.length >= 2);

  return (
    <div className="explorer-pf">
      {/* ---- Selected player badges ---- */}
      {players.length > 0 && (
        <div className="explorer-pf__badges">
          {players.map(p => (
            <span key={p} className="explorer-pf__badge" title={p}>
              <span className="explorer-pf__badge-icon" aria-hidden>♟</span>
              <span className="explorer-pf__badge-name">{p}</span>
              <button
                type="button"
                className="explorer-pf__badge-remove"
                onClick={() => onRemove(p)}
                aria-label={`Remove ${p}`}
              >
                <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" aria-hidden>
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </span>
          ))}
        </div>
      )}

      {/* ---- Input or trigger button ---- */}
      <div className="explorer-pf__row" ref={wrapRef}>
        {open ? (
          <input
            ref={inputRef}
            type="text"
            className="explorer-pf__input"
            value={query}
            onChange={e => handleChange(e.target.value)}
            onKeyDown={e => e.key === 'Escape' && setOpen(false)}
            placeholder={players.length === 0 ? 'Filter by player…' : 'Add spelling variant…'}
            aria-label="Search player"
            aria-autocomplete="list"
          />
        ) : (
          <button
            type="button"
            className={`explorer-pf__trigger${players.length > 0 ? ' explorer-pf__trigger--add' : ''}`}
            onClick={() => setOpen(true)}
          >
            {players.length === 0 ? (
              <>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden>
                  <circle cx="11" cy="11" r="8" />
                  <line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
                Filter by player
              </>
            ) : (
              '+ Add spelling'
            )}
          </button>
        )}
      </div>

      {/* ---- Portal dropdown ---- */}
      {showDropdown && anchor && (
        <Dropdown
          suggestions={suggestions}
          loading={loading}
          query={query}
          anchor={anchor}
          onSelect={handleSelect}
        />
      )}
    </div>
  );
}
