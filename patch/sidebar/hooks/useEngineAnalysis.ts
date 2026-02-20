import { useState, useEffect, useRef } from 'react';
import { analyzeAuto } from '../../engine/client';
import { stopAnalysis } from '../../engine/wasm/stockfish';
import type { EngineLine, EngineSource } from '../../engine/types';
import { cancelPrecompute } from '../../engine/precompute';
import { FALLBACK_BACKOFF_MS } from '../utils/config';

// Matches WASM_MOVETIME_MS in client.ts — kept in sync manually
const WASM_MOVETIME_MS = 8000;

export interface UseEngineAnalysisOptions {
  enabled: boolean;
  fen: string;
  multipv: number;
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
  const pollRef = useRef<number | null>(null);
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
      setEngineOrigin('stockfishWASM');
      // Compute knps (Lichess style: nodes / millis)
      if (analysis.nodes && analysis.millis && analysis.millis > 0) {
        setNps(Math.round(analysis.nodes / analysis.millis));
      }
    };

    try {
      const result = await analyzeAuto(targetFen, multipv, onUpdate);
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

  // Main analysis effect with polling
  useEffect(() => {
    if (!enabled) return;

    // When fen/multipv changes: immediately stop the running engine and
    // release the inFlight lock so the new position can start right away.
    stopAnalysis();
    inFlightRef.current = false;
    cancelPrecompute();
    lastPrecomputeParamsRef.current = { fen, multipv };

    analyzePosition(fen);
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(() => {
      analyzePosition(fen);
    }, 2000);

    return () => {
      stopAnalysis();
      inFlightRef.current = false;
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [enabled, fen, multipv]);

  // Reset state when disabled
  useEffect(() => {
    if (enabled) return;
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
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
  }, [enabled, fen, multipv]);

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
