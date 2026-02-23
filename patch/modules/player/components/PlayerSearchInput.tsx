// ============================================================
// PlayerSearchInput — 带 autocomplete 下拉的搜索框
// 下拉用 Portal 渲染到 body，避免被 overflow:hidden 的祖先裁剪
// ============================================================

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { usePlayerAutocomplete } from '../hooks/usePlayerAutocomplete';
import type { PlayerSuggestion } from '../types';

interface Props {
  /** Search button / Enter — goes to player list view */
  onSearch: (query: string) => void;
  /** Autocomplete item click — goes directly to games view */
  onPickPlayer: (exactName: string) => void;
  initialValue?: string;
}

function formatGames(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}

interface DropdownRect { top: number; left: number; width: number; }

export function PlayerSearchInput({ onSearch, onPickPlayer, initialValue = '' }: Props) {
  const [input, setInput] = useState(initialValue);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const [dropdownRect, setDropdownRect] = useState<DropdownRect | null>(null);

  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { suggestions, loading } = usePlayerAutocomplete(input);

  // 计算下拉框位置（相对 viewport，用 fixed 定位）
  const updateRect = useCallback(() => {
    if (!wrapRef.current) return;
    const r = wrapRef.current.getBoundingClientRect();
    setDropdownRect({ top: r.bottom + 8, left: r.left, width: r.width });
  }, []);

  // 点击外部关闭
  useEffect(() => {
    function onPointerDown(e: PointerEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('pointerdown', onPointerDown);
    return () => document.removeEventListener('pointerdown', onPointerDown);
  }, []);

  // 滚动/resize 时更新位置
  useEffect(() => {
    if (!open) return;
    window.addEventListener('scroll', updateRect, true);
    window.addEventListener('resize', updateRect);
    return () => {
      window.removeEventListener('scroll', updateRect, true);
      window.removeEventListener('resize', updateRect);
    };
  }, [open, updateRect]);

  // input 变化时展开、重置索引
  useEffect(() => {
    setActiveIdx(-1);
    if (input.length >= 2) {
      updateRect();
      setOpen(true);
    } else {
      setOpen(false);
    }
  }, [input, updateRect]);

  // Autocomplete item selected → go directly to games
  const commit = useCallback(
    (name: string) => {
      setInput(name);
      setOpen(false);
      setActiveIdx(-1);
      onPickPlayer(name);
    },
    [onPickPlayer],
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open) {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (input.trim()) onSearch(input.trim());
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIdx >= 0 && suggestions[activeIdx]) {
        commit(suggestions[activeIdx].name);
      } else if (input.trim()) {
        onSearch(input.trim());
        setOpen(false);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  const showDropdown = open && dropdownRect && (suggestions.length > 0 || loading);

  const dropdown = showDropdown && dropdownRect ? createPortal(
    <ul
      className="ps-dropdown"
      role="listbox"
      style={{
        position: 'fixed',
        top: dropdownRect.top,
        left: dropdownRect.left,
        width: dropdownRect.width,
      }}
    >
      {loading && suggestions.length === 0 && (
        <li className="ps-dropdown-loading">
          <span className="ps-spinner" />
          Searching…
        </li>
      )}
      {suggestions.map((s: PlayerSuggestion, i) => (
        <li
          key={s.name}
          className={`ps-dropdown-item${i === activeIdx ? ' is-active' : ''}`}
          role="option"
          aria-selected={i === activeIdx}
          onPointerDown={(e) => { e.preventDefault(); commit(s.name); }}
          onMouseEnter={() => setActiveIdx(i)}
        >
          <span className="ps-dropdown-name">{s.name}</span>
          <span className="ps-dropdown-games">{formatGames(s.games)} games</span>
        </li>
      ))}
    </ul>,
    document.body,
  ) : null;

  return (
    <div className="ps-search-wrap" ref={wrapRef}>
      <div className="ps-search-bar">
        <span className="ps-search-icon" aria-hidden>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </span>
        <input
          ref={inputRef}
          className="ps-search-input"
          type="text"
          placeholder="Lastname, Firstname — e.g. Li, Quanhao"
          value={input}
          autoComplete="off"
          spellCheck={false}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (input.length >= 2 && suggestions.length > 0) {
              updateRect();
              setOpen(true);
            }
          }}
          aria-autocomplete="list"
          aria-expanded={!!showDropdown}
        />
        {input && (
          <button
            className="ps-search-clear"
            aria-label="Clear"
            onClick={() => {
              setInput('');
              setOpen(false);
              inputRef.current?.focus();
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
        <button
          className="ps-search-btn"
          onClick={() => { if (input.trim()) { setOpen(false); onSearch(input.trim()); } }}
        >
          Search
        </button>
      </div>

      {dropdown}
    </div>
  );
}
