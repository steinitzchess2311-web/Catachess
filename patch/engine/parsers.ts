import type { EngineLine } from './types';

export function parseLichessCloudEval(data: any): EngineLine[] {
  if (!data || !Array.isArray(data.pvs)) return [];
  return data.pvs.map((pv: any, index: number) => ({
    multipv: index + 1,
    score: pv.mate != null ? `mate${pv.mate}` : pv.cp ?? 0,
    pv: typeof pv.moves === 'string' ? pv.moves.split(' ') : [],
  }));
}

export type SfEntry = {
  depth: number;
  multipv: number;
  score: number | string;
  pv: string[];
  nodes?: number;
  millis?: number;
};

export function parseSfInfoLine(line: string): SfEntry | null {
  if (!line.startsWith('info')) return null;
  const tokens = line.trim().split(/\s+/);
  const depthIndex = tokens.indexOf('depth');
  const multipvIndex = tokens.indexOf('multipv');
  const scoreIndex = tokens.indexOf('score');
  const pvIndex = tokens.indexOf('pv');
  if (depthIndex === -1 || multipvIndex === -1 || scoreIndex === -1 || pvIndex === -1) {
    return null;
  }

  const depth = Number(tokens[depthIndex + 1]);
  const multipv = Number(tokens[multipvIndex + 1]);
  const scoreType = tokens[scoreIndex + 1];
  const scoreVal = tokens[scoreIndex + 2];
  const pvMoves = tokens.slice(pvIndex + 1);
  if (!depth || !multipv || pvMoves.length === 0) return null;

  let score: number | string = 0;
  if (scoreType === 'cp') {
    const cp = Number(scoreVal);
    score = Number.isFinite(cp) ? cp : 0;
  } else if (scoreType === 'mate') {
    score = `mate${scoreVal}`;
  }

  const nodesIndex = tokens.indexOf('nodes');
  const timeIndex = tokens.indexOf('time');
  const nodes = nodesIndex !== -1 ? Number(tokens[nodesIndex + 1]) : undefined;
  const millis = timeIndex !== -1 ? Number(tokens[timeIndex + 1]) : undefined;

  return { depth, multipv, score, pv: pvMoves, nodes, millis };
}

export function parseSfCatachess(data: any): EngineLine[] {
  if (!data || !Array.isArray(data.info)) return [];
  const entries = data.info
    .map((line: string) => parseSfInfoLine(line))
    .filter((entry): entry is SfEntry => Boolean(entry));

  if (entries.length === 0) return [];

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

  return Array.from(perMultipv.values())
    .sort((a, b) => a.multipv - b.multipv)
    .map((entry) => ({
      multipv: entry.multipv,
      score: entry.score,
      pv: entry.pv,
    }));
}
