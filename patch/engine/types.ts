export type EngineScore = number | string;

export interface EngineLine {
  multipv: number;
  score: EngineScore;
  pv: string[];
}

export type EngineSource = 'backend' | 'lichess-cloud' | 'sf-catachess' | 'stockfish-wasm';

export interface EngineAnalysis {
  source: EngineSource;
  lines: EngineLine[];
  origin?: 'browser DB' | 'indexDB' | 'mongoDB' | 'lichessCloud' | 'stockfishWASM' | 'SFCata';
  currentDepth?: number;
  nodes?: number;
  millis?: number;
}
