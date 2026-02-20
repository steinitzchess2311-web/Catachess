import type { EngineAnalysis, EngineLine } from '../types';
import { parseSfInfoLine, type SfEntry } from '../parsers';

const DEFAULT_SCRIPT_URL = '/assets/stockfish/stockfish-lite-single.js';
const DEFAULT_WASM_URL = '/assets/stockfish/stockfish-lite-single.wasm';
// movetime sent to engine; JS timeout adds a buffer on top
const DEFAULT_MOVETIME_MS = 8000;
const JS_TIMEOUT_BUFFER_MS = 5000;

type StockfishModule = {
  listener?: (line: string) => void;
  processCommand?: (cmd: string) => void;
  ccall?: (...args: any[]) => any;
};

type StockfishFactory = (options: Record<string, any>) => Promise<StockfishModule>;
type EngineBackend =
  | { kind: 'worker'; worker: Worker }
  | { kind: 'module'; module: StockfishModule };

let factoryPromise: Promise<StockfishFactory> | null = null;
let modulePromise: Promise<StockfishModule> | null = null;
let workerPromise: Promise<Worker> | null = null;
let workerInstance: Worker | null = null;
let loadedModule: StockfishModule | null = null;
let runQueue: Promise<EngineAnalysis> = Promise.resolve({ source: 'stockfish-wasm', lines: [] });
let wasmCurrentlyRunning = false;

export function isWasmFree(): boolean {
  return !wasmCurrentlyRunning;
}

/**
 * Send "stop" to the engine immediately. If an analysis is running,
 * the engine will emit "bestmove" within ~5ms, resolving the current
 * runQueue entry and allowing the next queued analysis to start.
 */
export function stopAnalysis(): void {
  if (!wasmCurrentlyRunning) return;
  if (workerInstance) {
    workerInstance.postMessage('stop');
    return;
  }
  if (loadedModule) {
    sendCommandToModule(loadedModule, 'stop');
  }
}

function resolveEnv(name: string): string | undefined {
  try {
    const env = (import.meta as any)?.env;
    return env ? env[name] : undefined;
  } catch {
    return undefined;
  }
}

function resolveScriptUrl(): string {
  return resolveEnv('VITE_STOCKFISH_WASM_SCRIPT_URL') || DEFAULT_SCRIPT_URL;
}

function resolveWasmUrl(): string {
  return resolveEnv('VITE_STOCKFISH_WASM_BIN_URL') || DEFAULT_WASM_URL;
}

function loadScript(url: string): Promise<HTMLScriptElement> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = url;
    script.async = true;
    script.onload = () => resolve(script);
    script.onerror = () => reject(new Error(`Failed to load Stockfish script: ${url}`));
    document.head.appendChild(script);
  });
}

async function loadFactory(): Promise<StockfishFactory> {
  if (factoryPromise) return factoryPromise;

  factoryPromise = (async () => {
    const scriptUrl = resolveScriptUrl();
    const script = await loadScript(scriptUrl);
    const exported = (script as any)._exports || (window as any).Stockfish;
    if (!exported) {
      throw new Error('Stockfish factory not found after loading script');
    }
    return exported as StockfishFactory;
  })();

  return factoryPromise;
}

async function loadModule(): Promise<StockfishModule> {
  if (modulePromise) return modulePromise;

  modulePromise = (async () => {
    const factory = await loadFactory();
    const wasmUrl = resolveWasmUrl();
    const module = await factory({
      locateFile: (path: string) => {
        if (path.endsWith('.wasm')) return wasmUrl;
        return path;
      },
    });

    if (!module.processCommand && !module.ccall) {
      throw new Error('Stockfish module missing processCommand/ccall');
    }

    loadedModule = module;
    return module;
  })();

  return modulePromise;
}

async function loadWorker(): Promise<Worker> {
  if (workerPromise) return workerPromise;

  workerPromise = new Promise<Worker>((resolve, reject) => {
    let worker: Worker | null = null;
    let settled = false;
    const scriptUrl = resolveScriptUrl();
    // stockfish-lite-single.js detects Worker mode via `onmessage` presence +
    // absence of window.document; it derives the WASM URL automatically from
    // the script path (replaces .js with .wasm). No hash fragment needed.
    const workerUrl = scriptUrl;

    const cleanup = () => {
      if (!worker) return;
      worker.removeEventListener('message', onMessage);
      worker.removeEventListener('error', onError);
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };

    const fail = (message: string) => {
      if (settled) return;
      settled = true;
      cleanup();
      if (worker) {
        try {
          worker.terminate();
        } catch {
          // ignore
        }
      }
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

    const onError = () => {
      fail('Stockfish WASM worker failed to initialize');
    };

    let timeoutId: number | null = null;

    try {
      worker = new Worker(workerUrl);
      worker.addEventListener('message', onMessage);
      worker.addEventListener('error', onError);
      worker.postMessage('uci');
      timeoutId = window.setTimeout(() => {
        fail('Stockfish WASM worker initialization timeout');
      }, 10000);
    } catch {
      fail('Stockfish WASM worker creation failed');
    }
  });

  return workerPromise;
}

async function loadBackend(): Promise<EngineBackend> {
  try {
    const worker = await loadWorker();
    return { kind: 'worker', worker };
  } catch (error) {
    console.warn('[ENGINE WASM] Worker unavailable, falling back to main thread module:', error);
    const module = await loadModule();
    return { kind: 'module', module };
  }
}

function buildLines(entries: SfEntry[]): { lines: EngineLine[]; nodes?: number; millis?: number } {
  if (entries.length === 0) return { lines: [] };
  const maxDepth = Math.max(...entries.map((e) => e.depth));
  const perMultipv = new Map<number, SfEntry>();

  for (const entry of entries) {
    if (entry.depth !== maxDepth) continue;
    const existing = perMultipv.get(entry.multipv);
    if (!existing || entry.depth >= existing.depth) {
      perMultipv.set(entry.multipv, entry);
    }
  }

  if (perMultipv.size === 0) {
    for (const entry of entries) {
      const existing = perMultipv.get(entry.multipv);
      if (!existing || entry.depth > existing.depth) {
        perMultipv.set(entry.multipv, entry);
      }
    }
  }

  // Take nodes/millis from the last seen entry at maxDepth (most recent timing info)
  const lastEntry = entries[entries.length - 1];
  const nodes = lastEntry?.nodes;
  const millis = lastEntry?.millis;

  const lines = Array.from(perMultipv.values())
    .sort((a, b) => a.multipv - b.multipv)
    .map((entry) => ({
      multipv: entry.multipv,
      score: entry.score,
      pv: entry.pv,
    }));

  return { lines, nodes, millis };
}

function sendCommandToModule(module: StockfishModule, cmd: string): void {
  if (module.processCommand) {
    module.processCommand(cmd);
    return;
  }
  if (module.ccall) {
    module.ccall('command', null, ['string'], [cmd]);
  }
}

function sendCommand(backend: EngineBackend, cmd: string): void {
  if (backend.kind === 'worker') {
    backend.worker.postMessage(cmd);
    return;
  }
  sendCommandToModule(backend.module, cmd);
}

async function runAnalysis(
  fen: string,
  multipv: number,
  movetimeMs: number,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void
): Promise<EngineAnalysis> {
  wasmCurrentlyRunning = true;
  const backend = await loadBackend();
  const entries: SfEntry[] = [];

  try {
    return await new Promise<EngineAnalysis>((resolve, reject) => {
      let finished = false;
      let lastReportedDepth = 0;
      let workerMessageHandler: ((event: MessageEvent) => void) | null = null;
      let workerErrorHandler: ((event: ErrorEvent) => void) | null = null;

      // JS timeout = movetime + buffer (engine should stop itself via bestmove first)
      const timeout = setTimeout(() => {
        if (finished) return;
        finished = true;
        reject(new Error('Stockfish WASM timeout'));
      }, movetimeMs + JS_TIMEOUT_BUFFER_MS);

      const cleanup = () => {
        clearTimeout(timeout);
        if (backend.kind === 'module') {
          backend.module.listener = undefined;
          return;
        }
        if (workerMessageHandler) {
          backend.worker.removeEventListener('message', workerMessageHandler);
          workerMessageHandler = null;
        }
        if (workerErrorHandler) {
          backend.worker.removeEventListener('error', workerErrorHandler);
          workerErrorHandler = null;
        }
      };

      const handleLine = (line: string) => {
        if (!line) return;
        if (line.startsWith('info ')) {
          const parsed = parseSfInfoLine(line);
          if (parsed) {
            entries.push(parsed);
            // Fire onUpdate when we see exactly the last expected multipv line at a new depth
            // Matches Lichess Protocol: if (multiPv === this.expectedPvs)
            if (parsed.multipv === multipv && parsed.depth > lastReportedDepth) {
              lastReportedDepth = parsed.depth;
              if (onUpdate) {
                const { lines, nodes, millis } = buildLines(entries);
                if (lines.length > 0) {
                  onUpdate(
                    { source: 'stockfish-wasm', lines, currentDepth: parsed.depth, nodes, millis },
                    parsed.depth
                  );
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
        workerMessageHandler = (event: MessageEvent) => {
          if (typeof event.data !== 'string') return;
          handleLine(event.data);
        };
        workerErrorHandler = () => {
          if (finished) return;
          finished = true;
          cleanup();
          reject(new Error('Stockfish WASM worker crashed'));
        };
        backend.worker.addEventListener('message', workerMessageHandler);
        backend.worker.addEventListener('error', workerErrorHandler);
      }

      try {
        sendCommand(backend, `setoption name MultiPV value ${multipv}`);
        sendCommand(backend, 'ucinewgame');
        sendCommand(backend, `position fen ${fen}`);
        sendCommand(backend, `go movetime ${movetimeMs}`);
      } catch (error) {
        if (finished) return;
        finished = true;
        cleanup();
        reject(error instanceof Error ? error : new Error('Stockfish WASM failed'));
      }
    });
  } finally {
    wasmCurrentlyRunning = false;
  }
}

export async function analyzeWithWasm(
  fen: string,
  multipv: number,
  movetimeMs: number = DEFAULT_MOVETIME_MS,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void
): Promise<EngineAnalysis> {
  // Interrupt any currently running analysis so it resolves immediately
  // (engine emits "bestmove" in <5ms), allowing this new request to start ASAP.
  stopAnalysis();
  const run = runQueue.then(() => runAnalysis(fen, multipv, movetimeMs, onUpdate));
  runQueue = run.catch(() => ({ source: 'stockfish-wasm', lines: [] }));
  return run;
}
