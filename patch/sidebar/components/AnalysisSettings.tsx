/*
Created at: 2026-07-08 23:10 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:10 EDT
Last Modified by: Codex

Plain engine settings controls for analysis sidebars.
*/

import React from 'react';
import type { EngineMode } from '../../engine/types';

export interface AnalysisSettingsProps {
  currentDepth: number | null;
  nps: number | null;
  multipv: number;
  onMultipvChange: (multipv: number) => void;
  engineMode: EngineMode;
  onEngineModeChange: (engineMode: EngineMode) => void;
  engineEnabled: boolean;
  onEngineEnabledChange: (enabled: boolean) => void;
}

function formatNps(knps: number | null): string {
  if (knps === null) return '';
  if (knps >= 1000) return ` · ${(knps / 1000).toFixed(knps >= 10000 ? 0 : 1)} Mn/s`;
  return ` · ${Math.round(knps)} kn/s`;
}

export function AnalysisSettings({
  currentDepth,
  nps,
  multipv,
  onMultipvChange,
  engineMode,
  onEngineModeChange,
  engineEnabled,
  onEngineEnabledChange,
}: AnalysisSettingsProps) {
  return (
    <div className="patch-analysis-settings">
      <div className="patch-analysis-field">
        <span className="patch-analysis-label">Depth</span>
        <span className="patch-analysis-value">
          {currentDepth !== null ? `${currentDepth}${formatNps(nps)}` : '--'}
        </span>
      </div>
      <div className="patch-analysis-field">
        <span className="patch-analysis-label">Lines</span>
        <select value={multipv} onChange={(e) => onMultipvChange(Number(e.target.value))}>
          {[1, 2, 3, 4, 5].map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>
      <div className="patch-analysis-toggle">
        <label className="patch-toggle">
          <input
            type="checkbox"
            checked={engineEnabled}
            onChange={(e) => onEngineEnabledChange(e.target.checked)}
            aria-label="Engine"
          />
          <span className="patch-toggle-track" />
        </label>
      </div>
      <div className="patch-analysis-field">
        <span className="patch-analysis-label">Engine</span>
        <select
          value={engineMode}
          onChange={(e) => onEngineModeChange(e.target.value as EngineMode)}
          aria-label="Engine mode"
        >
          <option value="auto">Auto</option>
          <option value="stockfish">Stockfish</option>
          <option value="alphazero">AlphaZero</option>
        </select>
      </div>
    </div>
  );
}
