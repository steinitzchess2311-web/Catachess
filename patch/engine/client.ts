import type { EngineAnalysis } from './types';
import { parseLichessCloudEval } from './parsers';

const LICHESS_URL = 'https://lichess.org/api/cloud-eval';

function resolveEnv(name: string): string | undefined {
  try {
    const env = (import.meta as any)?.env;
    return env ? env[name] : undefined;
  } catch {
    return undefined;
  }
}

const API_BASE = resolveEnv('VITE_API_BASE') || '';

export async function analyzeWithFallback(
  fen: string,
  depth: number,
  multipv: number
): Promise<EngineAnalysis> {
  const params = new URLSearchParams({
    fen,
    multiPv: String(multipv),
  });
  const lichessResp = await fetch(`${LICHESS_URL}?${params.toString()}`);

  if (lichessResp.status === 404 || lichessResp.status === 429) {
    const resp = await fetch(`${API_BASE}/api/engine/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fen, depth, multipv }),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(text || `Engine error (${resp.status})`);
    }
    const data = await resp.json();
    return { source: 'backend', lines: Array.isArray(data.lines) ? data.lines : [] };
  }

  if (!lichessResp.ok) {
    const text = await lichessResp.text();
    throw new Error(text || `Engine error (${lichessResp.status})`);
  }

  const data = await lichessResp.json();
  const lines = parseLichessCloudEval(data);
  return { source: 'lichess-cloud', lines };
}
