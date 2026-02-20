/**
 * loader.ts — Stockfish WASM backend initialisation.
 *
 * Tries to create a Web Worker first (off-main-thread, preferred).
 * Falls back to loading the same script as a main-thread module if the
 * Worker fails (e.g. CSP restrictions, WASM compile timeout).
 *
 * The stockfish-lite-single.js build detects its execution context via:
 *   typeof onmessage !== 'undefined' && window.document === undefined
 * so no hash fragment is needed in the Worker URL; the WASM path is
 * derived automatically from the script URL (replaces .js → .wasm).
 */

import type { SfEntry } from '../parsers';
import { parseSfInfoLine } from '../parsers';

// ── Types ─────────────────────────────────────────────────────────────────────

export type StockfishModule = {
  listener?: (line: string) => void;
  processCommand?: (cmd: string) => void;
  ccall?: (...args: unknown[]) => unknown;
};

type StockfishFactory = (options: Record<string, unknown>) => Promise<StockfishModule>;

export type EngineBackend =
  | { kind: 'worker'; worker: Worker }
  | { kind: 'module'; module: StockfishModule };

// ── Singleton state ───────────────────────────────────────────────────────────

let factoryPromise: Promise<StockfishFactory> | null = null;
let modulePromise: Promise<StockfishModule> | null = null;
let workerPromise: Promise<Worker> | null = null;

export let workerInstance: Worker | null = null;
export let loadedModule: StockfishModule | null = null;

const WORKER_INIT_TIMEOUT_MS = 10_000;

// ── Env helpers ───────────────────────────────────────────────────────────────

function resolveEnv(name: string): string | undefined {
  try {
    const env = (import.meta as any)?.env;
    return env ? env[name] : undefined;
  } catch {
    return undefined;
  }
}

export function resolveScriptUrl(): string {
  return resolveEnv('VITE_STOCKFISH_WASM_SCRIPT_URL') ?? '/assets/stockfish/stockfish-lite-single.js';
}

export function resolveWasmUrl(): string {
  return resolveEnv('VITE_STOCKFISH_WASM_BIN_URL') ?? '/assets/stockfish/stockfish-lite-single.wasm';
}

// ── Script loading ────────────────────────────────────────────────────────────

function loadScript(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load Stockfish script: ${url}`));
    document.head.appendChild(script);
  });
}

async function loadFactory(): Promise<StockfishFactory> {
  if (factoryPromise) return factoryPromise;
  factoryPromise = (async () => {
    const scriptUrl = resolveScriptUrl();
    await loadScript(scriptUrl);
    const exported = (window as any).Stockfish;
    if (!exported) throw new Error('Stockfish factory not found after loading script');
    return exported as StockfishFactory;
  })();
  return factoryPromise;
}

// ── Module (main-thread fallback) ─────────────────────────────────────────────

async function loadModule(): Promise<StockfishModule> {
  if (modulePromise) return modulePromise;
  modulePromise = (async () => {
    const factory = await loadFactory();
    const wasmUrl = resolveWasmUrl();
    const module = await factory({
      locateFile: (path: string) => (path.endsWith('.wasm') ? wasmUrl : path),
    });
    if (!module.processCommand && !module.ccall) {
      throw new Error('Stockfish module missing processCommand/ccall');
    }
    loadedModule = module;
    return module;
  })();
  return modulePromise;
}

// ── Worker (preferred) ────────────────────────────────────────────────────────

async function loadWorker(): Promise<Worker> {
  if (workerPromise) return workerPromise;
  workerPromise = new Promise<Worker>((resolve, reject) => {
    let worker: Worker | null = null;
    let settled = false;
    // No hash fragment needed; the script detects Worker mode via
    // `typeof onmessage !== 'undefined' && window.document === undefined`
    // and derives the WASM URL from its own pathname (.js → .wasm).
    const scriptUrl = resolveScriptUrl();

    const cleanup = () => {
      worker?.removeEventListener('message', onMessage);
      worker?.removeEventListener('error', onError);
      if (timeoutId !== null) window.clearTimeout(timeoutId);
    };

    const fail = (message: string) => {
      if (settled) return;
      settled = true;
      cleanup();
      try { worker?.terminate(); } catch { /* ignore */ }
      workerPromise = null;
      reject(new Error(message));
    };

    const onMessage = (event: MessageEvent) => {
      if (settled || typeof event.data !== 'string') return;
      if (event.data === 'uciok') {
        settled = true;
        cleanup();
        workerInstance = worker;
        resolve(worker!);
      }
    };

    const onError = (e: ErrorEvent) => {
      fail(`Stockfish WASM worker error: ${e.message || 'unknown'}`);
    };

    let timeoutId: number | null = null;
    try {
      worker = new Worker(scriptUrl);
      worker.addEventListener('message', onMessage);
      worker.addEventListener('error', onError);
      worker.postMessage('uci');
      timeoutId = window.setTimeout(() => fail('Stockfish WASM worker initialization timeout'), WORKER_INIT_TIMEOUT_MS);
    } catch {
      fail('Stockfish WASM worker creation failed');
    }
  });
  return workerPromise;
}

// ── Backend selection ─────────────────────────────────────────────────────────

let backendPromise: Promise<EngineBackend> | null = null;

export async function loadBackend(): Promise<EngineBackend> {
  if (backendPromise) return backendPromise;
  backendPromise = (async () => {
    try {
      const worker = await loadWorker();
      return { kind: 'worker', worker } satisfies EngineBackend;
    } catch (error) {
      console.warn('[ENGINE WASM] Worker unavailable, falling back to main thread module:', error);
      const module = await loadModule();
      return { kind: 'module', module } satisfies EngineBackend;
    }
  })();
  return backendPromise;
}

// ── Command dispatch ──────────────────────────────────────────────────────────

export function sendCommandToModule(module: StockfishModule, cmd: string): void {
  if (module.processCommand) { module.processCommand(cmd); return; }
  if (module.ccall) module.ccall('command', null, ['string'], [cmd]);
}

export function sendCommand(backend: EngineBackend, cmd: string): void {
  if (backend.kind === 'worker') { backend.worker.postMessage(cmd); return; }
  sendCommandToModule(backend.module, cmd);
}

