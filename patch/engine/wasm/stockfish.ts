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

let factoryPromise: Promise<StockfishFactory> | null = null;
let modulePromise: Promise<StockfishModule> | null = null;
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
  if (loadedModule && wasmCurrentlyRunning) {
    sendCommand(loadedModule, 'stop');
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

function sendCommand(module: StockfishModule, cmd: string): void {
  if (module.processCommand) {
    module.processCommand(cmd);
    return;
  }
  if (module.ccall) {
    module.ccall('command', null, ['string'], [cmd]);
  }
}

async function runAnalysis(
  fen: string,
  multipv: number,
  movetimeMs: number,
  onUpdate?: (analysis: EngineAnalysis, currentDepth: number) => void
): Promise<EngineAnalysis> {
  wasmCurrentlyRunning = true;
  const module = await loadModule();
  const entries: SfEntry[] = [];

  try {
    return await new Promise<EngineAnalysis>((resolve, reject) => {
      let finished = false;
      let lastReportedDepth = 0;

      // JS timeout = movetime + buffer (engine should stop itself via bestmove first)
      const timeout = setTimeout(() => {
        if (finished) return;
        finished = true;
        reject(new Error('Stockfish WASM timeout'));
      }, movetimeMs + JS_TIMEOUT_BUFFER_MS);

      const cleanup = () => {
        clearTimeout(timeout);
        module.listener = undefined;
      };

      module.listener = (line: string) => {
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

      try {
        sendCommand(module, `setoption name MultiPV value ${multipv}`);
        sendCommand(module, 'ucinewgame');
        sendCommand(module, `position fen ${fen}`);
        sendCommand(module, `go movetime ${movetimeMs}`);
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
