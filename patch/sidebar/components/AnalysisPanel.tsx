import React from 'react';
import type { EngineLine } from '../../engine/types';
import { formatScore } from '../utils/formatters';

export interface AnalysisPanelProps {
  engineEnabled: boolean;
  lines: Array<EngineLine & { sanText?: string }>;
  status: 'idle' | 'running' | 'ready' | 'error';
  health: 'unknown' | 'ok' | 'down';
  error: string | null;
  lastUpdated: number | null;
  engineOrigin: string | null;
  turn?: 'w' | 'b';
}

function scoreTone(score: EngineLine['score']): 'good' | 'equal' | 'bad' {
  if (typeof score === 'string') {
    return score.startsWith('mate-') ? 'bad' : 'good';
  }
  if (score > 50) return 'good';
  if (score < -50) return 'bad';
  return 'equal';
}

export function AnalysisPanel({
  engineEnabled,
  lines,
  status,
  health,
  error,
  lastUpdated,
  engineOrigin,
  turn = 'w',
}: AnalysisPanelProps) {
  const primaryLine = lines[0] || null;
  const primaryScore = primaryLine ? formatScore(primaryLine.score) : '--';
  const primaryTone = primaryLine ? scoreTone(primaryLine.score) : 'equal';

  return (
    <div className="patch-analysis-panel">
      <div className="patch-analysis-hero">
        <div>
          <div className="patch-analysis-kicker">Position engine</div>
          <h3 className="patch-analysis-title">Stockfish analysis</h3>
        </div>
        <div className="patch-analysis-primary-score" data-tone={primaryTone}>
          {primaryScore}
        </div>
      </div>
      <div className="patch-analysis-status">
        <span className={`patch-analysis-badge is-${status}`}>{status}</span>
        <span className={`patch-analysis-health is-${health}`}>
          {!engineEnabled
            ? 'Engine off'
            : health === 'ok'
              ? 'Engine ready'
              : health === 'down'
                ? 'Engine down'
                : 'Checking engine'}
        </span>
        {engineOrigin && <span className="patch-analysis-source">{engineOrigin}</span>}
        {lastUpdated && (
          <span className="patch-analysis-updated">
            {new Date(lastUpdated).toLocaleTimeString()}
          </span>
        )}
      </div>
      {error && <div className="patch-analysis-error">{error}</div>}
      <div className="patch-analysis-lines">
        {!engineEnabled && (
          <div className="patch-analysis-empty">No analysis yet. Turn on engine to analyze.</div>
        )}
        {engineEnabled && lines.length === 0 && (
          <div className="patch-analysis-empty">No analysis yet.</div>
        )}
        {lines.map((line, index) => (
          <div key={`pv-${line.multipv}`} className="patch-analysis-line">
            <div className="patch-analysis-line-rank">{line.multipv || index + 1}</div>
            <div className="patch-analysis-line-main">
              <div className="patch-analysis-line-head">
                <span>{index === 0 ? 'Best line' : 'Candidate'}</span>
                <strong className="patch-analysis-score" data-tone={scoreTone(line.score)}>
                  {formatScore(line.score, turn)}
                </strong>
              </div>
              <div className="patch-analysis-pv">
                {line.sanText || (line.pv?.join(' ') ?? '')}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
