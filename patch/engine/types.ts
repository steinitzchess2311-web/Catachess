/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Shared frontend engine analysis types.
*/

export type EngineScore = number | string;

export interface EngineLine {
  multipv: number;
  score: EngineScore;
  pv: string[];
}

export type EngineMode = 'auto' | 'stockfish' | 'alphazero';

export type EngineSource =
  | 'backend'
  | 'lichess-cloud'
  | 'sf-catachess'
  | 'stockfish-wasm'
  | 'local-stockfish'
  | 'alphazero';

export interface EngineAnalysis {
  source: EngineSource;
  lines: EngineLine[];
  origin?:
    | 'browser DB'
    | 'indexDB'
    | 'mongoDB'
    | 'lichessCloud'
    | 'stockfishWASM'
    | 'SFCata'
    | 'Stockfish'
    | 'AlphaZero';
  currentDepth?: number;
  nodes?: number;
  millis?: number;
}
