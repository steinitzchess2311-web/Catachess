/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Plain engine result panel for scores and principal variations.
*/

import React from 'react';
import type { EngineLine } from '../../engine/types';
import { formatScore } from '../utils/formatters';

export interface AnalysisPanelProps {
  engineEnabled: boolean;
  lines: Array<EngineLine & { sanText?: string }>;
  error: string | null;
  turn?: 'w' | 'b';
  engineLabel?: string;
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
  error,
  turn = 'w',
  engineLabel = 'Engine',
}: AnalysisPanelProps) {
  const primaryLine = lines[0] || null;
  const primaryScore = primaryLine ? formatScore(primaryLine.score) : '--';
  const primaryTone = primaryLine ? scoreTone(primaryLine.score) : 'equal';
  const hasLines = lines.length > 0;

  return (
    <div className="patch-analysis-panel">
      <div className="patch-analysis-summary">
        <h3 className="patch-analysis-title">{engineLabel}</h3>
        <div className="patch-analysis-primary-score" data-tone={primaryTone}>
          {primaryScore}
        </div>
      </div>
      {error && <div className="patch-analysis-error">{error}</div>}
      <div className="patch-analysis-lines">
        {!hasLines && (
          <div className="patch-analysis-empty">
            {engineEnabled ? 'No analysis yet.' : 'Turn on engine to analyze.'}
          </div>
        )}
        {lines.map((line, index) => (
          <div key={`pv-${line.multipv}`} className="patch-analysis-line">
            <div className="patch-analysis-line-rank">{line.multipv || index + 1}</div>
            <div className="patch-analysis-line-main">
              <div className="patch-analysis-line-head">
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
