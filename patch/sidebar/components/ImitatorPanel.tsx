/*
Created at: 2026-07-08 23:23 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:23 EDT
Last Modified by: Codex

Predictor result panel for Maia and Catie human move forecasts.
*/

import React from 'react';
import type { PredictorResult } from '../hooks/useImitator';
import { formatProbability } from '../utils/formatters';

export interface ImitatorPanelProps {
  result: PredictorResult;
}

export function ImitatorPanel({ result }: ImitatorPanelProps) {
  if (result.status === 'idle') {
    return (
      <div className="patch-analysis-panel patch-imitator-panel">
        <div className="patch-analysis-empty">
          Turn on predictor to estimate the next human move.
        </div>
      </div>
    );
  }

  const moves = Array.isArray(result.moves) ? result.moves : [];
  return (
    <div className="patch-analysis-panel patch-imitator-panel">
      <div className="patch-imitator-card">
        <div className="patch-imitator-header">
          <div>
            <div className="patch-imitator-title">
              {result.provider === 'maia' ? 'Maia predictor' : 'Catie predictor'}
            </div>
            <div className="patch-imitator-meta">
              {result.model || result.provider}
              {result.updated && (
                <span className="patch-imitator-updated">
                  {new Date(result.updated).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        </div>
        {result.error && (
          <div className="patch-analysis-error">
            {normalizePredictorError(result.error)}
          </div>
        )}
        <div className="patch-imitator-moves">
          {result.status === 'running' && <div className="patch-analysis-empty">Predicting...</div>}
          {result.status !== 'running' && moves.length === 0 && (
            <div className="patch-analysis-empty">No moves yet.</div>
          )}
          {moves.map((move, idx) => (
            <div key={`${move.uci || move.move}-${idx}`} className="patch-imitator-row">
              <div className="patch-imitator-prob">{formatProbability(move.probability)}</div>
              <div className="patch-imitator-move">
                <span>{move.san || move.move || move.uci}</span>
                {move.uci && move.san && move.uci !== move.san && (
                  <span className="patch-imitator-tags">{move.uci}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function normalizePredictorError(error: string): string {
  try {
    const parsed = JSON.parse(error);
    if (typeof parsed?.detail === 'string') return parsed.detail;
  } catch {
    // Keep plain transport errors readable without exposing parser details.
  }
  return error;
}
