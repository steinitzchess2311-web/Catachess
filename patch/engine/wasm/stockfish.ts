/**
 * stockfish.ts — public re-export surface for the WASM engine.
 *
 * Internal split:
 *   loader.ts   — backend initialisation (Worker / main-thread fallback)
 *   analysis.ts — UCI analysis runner + queue
 */

export { analyzeWithWasm, stopAnalysis, isWasmFree } from './analysis';
