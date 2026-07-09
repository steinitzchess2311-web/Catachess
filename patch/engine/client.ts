/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Frontend engine client for Auto/WASM and explicit server worker modes.
*/

import type { EngineAnalysis, EngineMode } from './types';
import { getCacheManager } from './cache';
import { generateCacheKey } from './cache/utils';
import { analyzeWithWasm } from './wasm/stockfish';

const IN_FLIGHT = new Map<string, Promise<EngineAnalysis>>();
const WASM_MOVETIME_MS = 8000;
// Synthetic depth key used for cache storage (movetime-based results stored under this key)
const WASM_CACHE_DEPTH = 99;
// Match Lichess: throttle UI updates to max 5x/sec
const ONUPDATE_THROTTLE_MS = 200;

function resolveEnv(name: string): string | undefined {
  try {
    const env = (import.meta as any)?.env;
    return env ? env[name] : undefined;
  } catch {
    return undefined;
  }
}

function resolveApiBase(): string {
  const envBase = resolveEnv('VITE_API_BASE');
  if (envBase) return envBase;
  try {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://localhost:7878';
    }
  } catch {
    // ignore
  }
  return 'https://api.catachess.com';
}

export const API_BASE = resolveApiBase();

function mapBackendSource(source: string | undefined): EngineAnalysis['source'] {
  if (!source) return 'backend';
  if (source === 'stockfish-wasm') return 'stockfish-wasm';
  if (source === 'lichess-cloud') return 'lichess-cloud';
  if (source === 'sf-catachess') return 'sf-catachess';
  if (source === 'local-stockfish') return 'local-stockfish';
  if (source === 'LocalStockfish') return 'local-stockfish';
  if (source === 'lc0') return 'lc0';
  if (source === 'LC0') return 'lc0';
  if (source === 'alphazero') return 'alphazero';
  if (source === 'AlphaZero') return 'alphazero';
  if (source === 'SFCata') return 'sf-catachess';
  if (source === 'CloudEval') return 'lichess-cloud';
  if (source === 'Fallback') return 'backend';
  return 'backend';
}


async function storeMongoCache(
  fen: string,
  depth: number,
  multipv: number,
  lines: any[],
  source: EngineAnalysis['source'],
  engineMode: EngineMode = 'auto'
): Promise<void> {
  await fetch(`${API_BASE}/api/engine/cache/store`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fen,
      depth,
      multipv,
      lines,
      source,
      engine_mode: engineMode,
    }),
  });
}

function backendEngineMode(mode: EngineMode): string {
  if (mode === 'stockfish') return 'stockfish';
  if (mode === 'lc0') return 'lc0';
  if (mode === 'alphazero') return 'alphazero';
  return 'sf';
}

function originForMode(mode: EngineMode, source: EngineAnalysis['source']): EngineAnalysis['origin'] {
  if (mode === 'stockfish' || source === 'local-stockfish') return 'Stockfish';
  if (mode === 'lc0' || source === 'lc0') return 'Leela/LC0';
  if (mode === 'alphazero' || source === 'alphazero') return 'AlphaZero';
  return 'SFCata';
}

async function callServerEngine(
  fen: string,
  depth: number,
  multipv: number,
  engineMode: EngineMode
): Promise<EngineAnalysis> {
  const resp = await fetch(`${API_BASE}/api/engine/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, depth, multipv, engine: backendEngineMode(engineMode) }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Engine error (${resp.status})`);
  }
  const data = await resp.json();

  // Log MongoDB cache metadata to console
  if (data.cache_metadata) {
    const meta = data.cache_metadata;
    if (meta.mongodb_hit) {
      console.log(
        `[MONGODB CACHE] ✓ HIT in ${meta.mongodb_query_ms}ms | ` +
        `hit_count=${meta.hit_count} | cached_at=${meta.cached_at} | ` +
        `total=${meta.total_ms}ms`
      );
    } else {
      console.log(
        `[MONGODB CACHE] ✗ MISS in ${meta.mongodb_query_ms}ms | ` +
        `engine=${meta.engine_ms}ms | store=${meta.mongodb_store_ms}ms | ` +
        `total=${meta.total_ms}ms`
      );
    }
  }

  return {
    source: mapBackendSource(data.source),
    lines: Array.isArray(data.lines) ? data.lines : [],
    origin: originForMode(engineMode, mapBackendSource(data.source)),
  };
}


// Depth used for SFCata backend requests
const SFCATA_DEPTH = 20;

export async function analyzeAuto(
  fen: string,
  multipv: number,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void,
  engineMode: EngineMode = 'auto'
): Promise<EngineAnalysis> {
  const cacheManager = getCacheManager();
  const cacheDepth = engineMode === 'auto' ? WASM_CACHE_DEPTH : SFCATA_DEPTH;
  const cacheKey = `${engineMode}:${generateCacheKey({ fen, depth: cacheDepth, multipv })}`;

  if (IN_FLIGHT.has(cacheKey)) {
    return IN_FLIGHT.get(cacheKey)!;
  }

  // Throttle onUpdate to max 5x/sec (Lichess: throttle(200ms))
  let lastEmitTime = 0;
  const throttledUpdate = onUpdate
    ? (analysis: EngineAnalysis, depth: number) => {
        const now = Date.now();
        if (now - lastEmitTime >= ONUPDATE_THROTTLE_MS) {
          lastEmitTime = now;
          onUpdate(analysis, depth);
        }
      }
    : undefined;

  const run = (async () => {
    if (engineMode === 'auto') {
      // Step 1: Stockfish WASM (time-based, streaming via onUpdate)
      try {
        const wasmResult = await analyzeWithWasm(fen, multipv, WASM_MOVETIME_MS, throttledUpdate);
        if (wasmResult.lines.length > 0) {
          const timestamp = Date.now();
          // Fire-and-forget: don't block result delivery on I/O
          cacheManager.set(
            { fen, depth: WASM_CACHE_DEPTH, multipv },
            { fen, depth: WASM_CACHE_DEPTH, multipv, lines: wasmResult.lines, source: wasmResult.source, timestamp }
          ).catch(() => {});
          storeMongoCache(fen, WASM_CACHE_DEPTH, multipv, wasmResult.lines, wasmResult.source, 'auto')
            .catch(e => console.warn('[ENGINE CLIENT] MongoDB store failed (wasm):', e));
          return { ...wasmResult, origin: 'stockfishWASM' as const };
        }
      } catch (error) {
        console.warn('[ENGINE CLIENT] Stockfish WASM failed:', error);
      }
    }

    // Step 2: server engine fallback or explicit server worker.
    cacheManager.recordNetworkCall();
    const sfResult = await callServerEngine(fen, SFCATA_DEPTH, multipv, engineMode);
    if (sfResult.lines.length > 0) {
      const timestamp = Date.now();
      // Fire-and-forget
      cacheManager.set(
        { fen, depth: cacheDepth, multipv },
        { fen, depth: cacheDepth, multipv, lines: sfResult.lines, source: sfResult.source, timestamp }
      ).catch(() => {});
      storeMongoCache(fen, cacheDepth, multipv, sfResult.lines, sfResult.source, engineMode)
        .catch(e => console.warn('[ENGINE CLIENT] MongoDB store failed (sfcata):', e));
    }

    return sfResult;
  })();

  IN_FLIGHT.set(cacheKey, run);
  try {
    return await run;
  } finally {
    IN_FLIGHT.delete(cacheKey);
  }
}

export async function analyzeWithFallback(
  fen: string,
  multipv: number,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void,
  engineMode: EngineMode = 'auto'
): Promise<EngineAnalysis> {
  return analyzeAuto(fen, multipv, onUpdate, engineMode);
}
