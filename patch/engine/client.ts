import type { EngineAnalysis } from './types';
import { getCacheManager } from './cache';
import { generateCacheKey } from './cache/utils';
import { analyzeWithWasm } from './wasm/stockfish';

const IN_FLIGHT = new Map<string, Promise<EngineAnalysis>>();
const WASM_MOVETIME_MS = 8000;
// Synthetic depth key used for cache storage (movetime-based results stored under this key)
const WASM_CACHE_DEPTH = 99;

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
  source: EngineAnalysis['source']
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
    }),
  });
}

async function callSfcata(
  fen: string,
  depth: number,
  multipv: number
): Promise<EngineAnalysis> {
  const resp = await fetch(`${API_BASE}/api/engine/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fen, depth, multipv, engine: 'sf' }),
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
    origin: 'SFCata',
  };
}


// Depth used for SFCata backend requests
const SFCATA_DEPTH = 20;

export async function analyzeAuto(
  fen: string,
  multipv: number,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void
): Promise<EngineAnalysis> {
  const cacheManager = getCacheManager();
  const cacheKey = generateCacheKey({ fen, depth: WASM_CACHE_DEPTH, multipv });

  if (IN_FLIGHT.has(cacheKey)) {
    return IN_FLIGHT.get(cacheKey)!;
  }

  const run = (async () => {
    // Step 1: Stockfish WASM (time-based, streaming via onUpdate)
    try {
      const wasmResult = await analyzeWithWasm(fen, multipv, WASM_MOVETIME_MS, onUpdate);
      if (wasmResult.lines.length > 0) {
        console.log('[ENGINE SOURCE] stockfishWASM');
        const timestamp = Date.now();
        await cacheManager.set(
          { fen, depth: WASM_CACHE_DEPTH, multipv },
          { fen, depth: WASM_CACHE_DEPTH, multipv, lines: wasmResult.lines, source: wasmResult.source, timestamp }
        );
        try {
          await storeMongoCache(fen, WASM_CACHE_DEPTH, multipv, wasmResult.lines, wasmResult.source);
        } catch (error) {
          console.warn('[ENGINE CLIENT] MongoDB store failed (wasm):', error);
        }
        return { ...wasmResult, origin: 'stockfishWASM' };
      }
    } catch (error) {
      console.warn('[ENGINE CLIENT] Stockfish WASM failed:', error);
    }

    // Step 2: SFCata fallback
    cacheManager.recordNetworkCall();
    const sfResult = await callSfcata(fen, SFCATA_DEPTH, multipv);
    console.log('[ENGINE SOURCE] SFCata');
    if (sfResult.lines.length > 0) {
      const timestamp = Date.now();
      await cacheManager.set(
        { fen, depth: WASM_CACHE_DEPTH, multipv },
        { fen, depth: WASM_CACHE_DEPTH, multipv, lines: sfResult.lines, source: sfResult.source, timestamp }
      );
      try {
        await storeMongoCache(fen, WASM_CACHE_DEPTH, multipv, sfResult.lines, sfResult.source);
      } catch (error) {
        console.warn('[ENGINE CLIENT] MongoDB store failed (sfcata):', error);
      }
    }

    return { ...sfResult, origin: 'SFCata' };
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
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void
): Promise<EngineAnalysis> {
  return analyzeAuto(fen, multipv, onUpdate);
}
