/**
 * analysis.ts — Stockfish WASM analysis runner.
 * Depends on loader.ts for backend initialisation.
 */

import type { EngineAnalysis, EngineLine } from '../types';
import { loadBackend, sendCommand, sendCommandToModule, workerInstance, loadedModule } from './loader';
import type { SfEntry } from '../parsers';
import { parseSfInfoLine } from '../parsers';

const DEFAULT_MOVETIME_MS = 8000;
const JS_TIMEOUT_BUFFER_MS = 5000;
// Throttle onUpdate to ≤5 times/sec (Lichess protocol)
const ONUPDATE_THROTTLE_MS = 200;

// Global serial queue — only one Stockfish analysis at a time
let runQueue: Promise<EngineAnalysis> = Promise.resolve({ source: 'stockfish-wasm', lines: [] });
let wasmCurrentlyRunning = false;

export function isWasmFree(): boolean {
  return !wasmCurrentlyRunning;
}

export function stopAnalysis(): void {
  if (!wasmCurrentlyRunning) return;
  if (workerInstance) { workerInstance.postMessage('stop'); return; }
  if (loadedModule) sendCommandToModule(loadedModule, 'stop');
}

// ── Line builder ──────────────────────────────────────────────────────────────

function buildLines(entries: SfEntry[]): { lines: EngineLine[]; nodes?: number; millis?: number } {
  if (entries.length === 0) return { lines: [] };
  const maxDepth = Math.max(...entries.map((e) => e.depth));
  const perMultipv = new Map<number, SfEntry>();

  for (const entry of entries) {
    if (entry.depth !== maxDepth) continue;
    const existing = perMultipv.get(entry.multipv);
    if (!existing || entry.depth >= existing.depth) perMultipv.set(entry.multipv, entry);
  }

  if (perMultipv.size === 0) {
    for (const entry of entries) {
      const existing = perMultipv.get(entry.multipv);
      if (!existing || entry.depth > existing.depth) perMultipv.set(entry.multipv, entry);
    }
  }

  const lastEntry = entries[entries.length - 1];
  const lines = Array.from(perMultipv.values())
    .sort((a, b) => a.multipv - b.multipv)
    .map((e) => ({ multipv: e.multipv, score: e.score, pv: e.pv }));

  return { lines, nodes: lastEntry?.nodes, millis: lastEntry?.millis };
}

// ── Core analysis ─────────────────────────────────────────────────────────────

async function runAnalysis(
  fen: string,
  multipv: number,
  movetimeMs: number,
  onUpdate?: (analysis: EngineAnalysis, depth: number) => void
): Promise<EngineAnalysis> {
  wasmCurrentlyRunning = true;
  const backend = await loadBackend();
  const entries: SfEntry[] = [];

  try {
    return await new Promise<EngineAnalysis>((resolve, reject) => {
      let finished = false;
      let lastReportedDepth = 0;
      let lastEmitTime = 0;
      let workerMsgHandler: ((e: MessageEvent) => void) | null = null;
      let workerErrHandler: (() => void) | null = null;

      const timeout = setTimeout(() => {
        if (finished) return;
        finished = true;
        reject(new Error('Stockfish WASM timeout'));
      }, movetimeMs + JS_TIMEOUT_BUFFER_MS);

      const cleanup = () => {
        clearTimeout(timeout);
        if (backend.kind === 'module') { backend.module.listener = undefined; return; }
        if (workerMsgHandler) backend.worker.removeEventListener('message', workerMsgHandler);
        if (workerErrHandler) backend.worker.removeEventListener('error', workerErrHandler);
      };

      const handleLine = (line: string) => {
        if (!line) return;
        if (line.startsWith('info ')) {
          const parsed = parseSfInfoLine(line);
          if (parsed) {
            entries.push(parsed);
            // Emit at each new depth when the last multipv line arrives, throttled
            if (parsed.multipv === multipv && parsed.depth > lastReportedDepth && onUpdate) {
              const now = Date.now();
              if (now - lastEmitTime >= ONUPDATE_THROTTLE_MS) {
                lastEmitTime = now;
                lastReportedDepth = parsed.depth;
                const { lines, nodes, millis } = buildLines(entries);
                if (lines.length > 0) {
                  onUpdate({ source: 'stockfish-wasm', lines, currentDepth: parsed.depth, nodes, millis }, parsed.depth);
                }
              }
            }
          }
          return;
        }
        if (line.startsWith('bestmove')) {
          if (finished) return;
          finished = true;
          cleanup();
          const { lines, nodes, millis } = buildLines(entries);
          resolve({ source: 'stockfish-wasm', lines, currentDepth: lastReportedDepth, nodes, millis });
        }
      };

      if (backend.kind === 'module') {
        backend.module.listener = handleLine;
      } else {
        workerMsgHandler = (e: MessageEvent) => { if (typeof e.data === 'string') handleLine(e.data); };
        workerErrHandler = () => { if (!finished) { finished = true; cleanup(); reject(new Error('Stockfish WASM worker crashed')); } };
        backend.worker.addEventListener('message', workerMsgHandler);
        backend.worker.addEventListener('error', workerErrHandler);
      }

      try {
        sendCommand(backend, `setoption name MultiPV value ${multipv}`);
        sendCommand(backend, 'ucinewgame');
        sendCommand(backend, `position fen ${fen}`);
        sendCommand(backend, `go movetime ${movetimeMs}`);
      } catch (error) {
        if (!finished) { finished = true; cleanup(); reject(error instanceof Error ? error : new Error('Stockfish command failed')); }
      }
    });
  } finally {
    wasmCurrentlyRunning = false;
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function analyzeWithWasm(
  fen: string,
  multipv: number,
  movetimeMs: number = DEFAULT_MOVETIME_MS,
  onUpdate?: (analysis: EngineAnalysis, depth: number) => void
): Promise<EngineAnalysis> {
  // Throttle onUpdate
  let lastEmit = 0;
  const throttled = onUpdate
    ? (analysis: EngineAnalysis, depth: number) => {
        const now = Date.now();
        if (now - lastEmit >= ONUPDATE_THROTTLE_MS) { lastEmit = now; onUpdate(analysis, depth); }
      }
    : undefined;

  stopAnalysis();
  const run = runQueue.then(() => runAnalysis(fen, multipv, movetimeMs, throttled));
  runQueue = run.catch(() => ({ source: 'stockfish-wasm' as const, lines: [] }));
  return run;
}
