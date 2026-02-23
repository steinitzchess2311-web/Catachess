// ============================================================
// Hook: 棋手名字自动补全（防抖 + AbortController）
// ============================================================

import { useState, useEffect, useRef } from 'react';
import { fetchPlayerSuggestions } from '../api';
import type { PlayerSuggestion } from '../types';

const DEBOUNCE_MS = 200;
const MIN_CHARS = 2;

export interface UsePlayerAutocompleteResult {
  suggestions: PlayerSuggestion[];
  loading: boolean;
}

export function usePlayerAutocomplete(query: string): UsePlayerAutocompleteResult {
  const [suggestions, setSuggestions] = useState<PlayerSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    abortRef.current?.abort();

    if (query.length < MIN_CHARS) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    setLoading(true);

    timerRef.current = setTimeout(() => {
      const controller = new AbortController();
      abortRef.current = controller;

      fetchPlayerSuggestions(query, 8, controller.signal)
        .then((data) => {
          setSuggestions(data.players);
          setLoading(false);
        })
        .catch((err: unknown) => {
          if ((err as Error)?.name === 'AbortError') return;
          setSuggestions([]);
          setLoading(false);
        });
    }, DEBOUNCE_MS);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      abortRef.current?.abort();
    };
  }, [query]);

  return { suggestions, loading };
}
