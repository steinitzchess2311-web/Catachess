/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

React hook for lifecycle-managed engine analysis.
*/

import { useState, useEffect, useRef } from 'react';
import { analyzeAuto } from '../../engine/client';
import { stopAnalysis } from '../../engine/wasm/stockfish';
import type { EngineLine, EngineMode, EngineSource } from '../../engine/types';
import { cancelPrecompute } from '../../engine/precompute';
import { FALLBACK_BACKOFF_MS } from '../utils/config';

// Matches WASM_MOVETIME_MS in client.ts — kept in sync manually
const WASM_MOVETIME_MS = 8000;

export interface UseEngineAnalysisOptions {
  enabled: boolean;
  fen: string;
  multipv: number;
  engineMode: EngineMode;
}

export interface UseEngineAnalysisResult {
  lines: EngineLine[];
  /** FEN that the current lines were computed for — null until first result arrives */
  analysisFen: string | null;
  status: 'idle' | 'running' | 'ready' | 'error';
  error: string | null;
  lastUpdated: number | null;
  health: 'unknown' | 'ok' | 'down';
  source: EngineSource | null;
  engineOrigin: string | null;
  currentDepth: number | null;
  nps: number | null;  // nodes per second (knps)
}

/**
 * Hook for managing engine analysis state with streaming depth updates
 */
export function useEngineAnalysis({
  enabled,
  fen,
  multipv,
  engineMode,
}: UseEngineAnalysisOptions): UseEngineAnalysisResult {
  const [lines, setLines] = useState<EngineLine[]>([]);
  const [analysisFen, setAnalysisFen] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'ready' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown');
  const [source, setSource] = useState<EngineSource | null>(null);
  const [engineOrigin, setEngineOrigin] = useState<string | null>(null);
  const [currentDepth, setCurrentDepth] = useState<number | null>(null);
  const [nps, setNps] = useState<number | null>(null);

  const inFlightRef = useRef(false);
  const debounceRef = useRef<number | null>(null);
  const nextAllowedRef = useRef<number>(0);
  const currentFenRef = useRef<string>(fen);
  const lastPrecomputeParamsRef = useRef<{
    fen: string;
    multipv: number;
  } | null>(null);

  // Keep current FEN ref in sync for stale callback detection
  useEffect(() => {
    currentFenRef.current = fen;
  }, [fen]);

  const analyzePosition = async (targetFen: string) => {
    if (!targetFen || inFlightRef.current) return;
    const now = Date.now();
    if (now < nextAllowedRef.current) return;

    inFlightRef.current = true;
    setStatus('running');
    setError(null);

    // onUpdate is called for each depth increment from WASM streaming
    const onUpdate = (analysis: { lines: any[]; source: any; currentDepth?: number; nodes?: number; millis?: number }, depth: number) => {
      // Ignore stale updates if FEN has changed
      if (currentFenRef.current !== targetFen) return;
      setLines(analysis.lines);
      setAnalysisFen(targetFen);
      setSource(analysis.source);
      setCurrentDepth(depth);
      setLastUpdated(Date.now());
      setHealth('ok');
      setStatus('ready');
      setEngineOrigin(engineMode === 'auto' ? 'stockfishWASM' : null);
      // Compute knps (Lichess style: nodes / millis)
      if (analysis.nodes && analysis.millis && analysis.millis > 0) {
        setNps(Math.round(analysis.nodes / analysis.millis));
      }
    };

    try {
      const result = await analyzeAuto(targetFen, multipv, onUpdate, engineMode);
      // Only apply if FEN hasn't changed and WASM hasn't already updated with a deeper result
      if (currentFenRef.current === targetFen) {
        setLines(result.lines);
        setAnalysisFen(targetFen);
        setSource(result.source);
        setEngineOrigin(result.origin ?? null);
        if (result.currentDepth) setCurrentDepth(result.currentDepth);
        if (result.nodes && result.millis && result.millis > 0) {
          setNps(Math.round(result.nodes / result.millis));
        }
        setStatus('ready');
        setLastUpdated(Date.now());
        setHealth('ok');
      }
    } catch (e: any) {
      if (e?.message?.includes('429')) {
        nextAllowedRef.current = Date.now() + FALLBACK_BACKOFF_MS;
      }
      if (currentFenRef.current === targetFen) {
        setStatus('error');
        setError(e?.message || 'Engine request failed');
        setHealth('down');
      }
    } finally {
      inFlightRef.current = false;
    }
  };

  // Main analysis effect with debounce — single request per FEN change.
  // Debounce: wait 150 ms before starting so rapid FEN changes (arrow-key
  // navigation) don't thrash the engine with start/stop cycles.
  // WASM engine already streams depth updates via onUpdate — no polling needed.
  useEffect(() => {
    if (!enabled) return;

    stopAnalysis();
    inFlightRef.current = false;
    cancelPrecompute();
    lastPrecomputeParamsRef.current = { fen, multipv };

    if (debounceRef.current) window.clearTimeout(debounceRef.current);

    debounceRef.current = window.setTimeout(() => {
      analyzePosition(fen);
    }, 150);

    return () => {
      if (debounceRef.current) { window.clearTimeout(debounceRef.current); debounceRef.current = null; }
      stopAnalysis();
      inFlightRef.current = false;
    };
  }, [enabled, fen, multipv, engineMode]);

  // Reset state when disabled
  useEffect(() => {
    if (enabled) return;
    setStatus('idle');
    setHealth('down');
    setLines([]);
    setAnalysisFen(null);
    setError(null);
    setLastUpdated(null);
    setSource(null);
    setEngineOrigin(null);
    setCurrentDepth(null);
    setNps(null);
  }, [enabled]);

  // Reset lines when parameters change
  useEffect(() => {
    if (!enabled) return;
    setLines([]);
    setAnalysisFen(null);
    setStatus('idle');
    setError(null);
    setSource(null);
    setEngineOrigin(null);
    setCurrentDepth(null);
    setNps(null);
  }, [enabled, fen, multipv, engineMode]);

  return {
    lines,
    analysisFen,
    status,
    error,
    lastUpdated,
    health,
    source,
    engineOrigin,
    currentDepth,
    nps,
  };
}
