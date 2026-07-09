/*
Created at: 2026-07-08 23:30 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:30 EDT
Last Modified by: Codex

React hook for Maia/Catie human move predictor requests.
*/

import { useState, useEffect, useRef } from 'react';
import { API_BASE } from '../../engine/client';

export type PredictorProvider = 'maia' | 'catie';

export interface PredictorMove {
  rank: number;
  move: string;
  uci?: string;
  san?: string;
  probability?: number;
  source?: string;
}

export interface PredictorResult {
  status: 'idle' | 'running' | 'ready' | 'error';
  provider: PredictorProvider;
  model?: string;
  moves: PredictorMove[];
  meta?: Record<string, any>;
  updated?: number;
  error?: string | null;
}

export interface UsePredictorOptions {
  enabled: boolean;
  fen: string;
  provider: PredictorProvider;
  topK: number;
  elo: number;
}

export interface UsePredictorResult {
  result: PredictorResult;
}

export function usePredictor({
  enabled,
  fen,
  provider,
  topK,
  elo,
}: UsePredictorOptions): UsePredictorResult {
  const [result, setResult] = useState<PredictorResult>({
    status: 'idle',
    provider,
    moves: [],
    error: null,
  });
  const requestRef = useRef(0);

  useEffect(() => {
    if (!enabled || !fen) {
      setResult({ status: 'idle', provider, moves: [], error: null });
      return;
    }

    const currentRequest = requestRef.current + 1;
    requestRef.current = currentRequest;
    setResult((prev) => {
      return {
        ...prev,
        provider,
        status: 'running',
        error: null,
      };
    });

    const run = async () => {
      try {
        const resp = await fetch(`${API_BASE}/api/predictor/predict`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider,
            fen,
            top_k: topK,
            elo,
          }),
        });
        if (!resp.ok) {
          const text = await resp.text();
          throw new Error(text || `Predictor error (${resp.status})`);
        }
        const data = await resp.json();
        if (requestRef.current !== currentRequest) return;
        setResult({
          status: 'ready',
          provider,
          model: data.model,
          moves: Array.isArray(data.moves) ? data.moves : [],
          meta: data.meta || {},
          updated: Date.now(),
          error: null,
        });
      } catch (e: any) {
        if (requestRef.current !== currentRequest) return;
        setResult({
          status: 'error',
          provider,
          moves: [],
          updated: Date.now(),
          error: e?.message || 'Predictor failed',
        });
      }
    };

    void run();
  }, [enabled, fen, provider, topK, elo]);

  return {
    result,
  };
}
