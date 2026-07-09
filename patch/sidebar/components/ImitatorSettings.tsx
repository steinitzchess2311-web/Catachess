/*
Created at: 2026-07-08 23:23 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:23 EDT
Last Modified by: Codex

Compact predictor controls for provider, output size, rating and run state.
*/

import React from 'react';
import type { PredictorProvider } from '../hooks/useImitator';

export interface ImitatorSettingsProps {
  provider: PredictorProvider;
  onProviderChange: (provider: PredictorProvider) => void;
  topK: number;
  onTopKChange: (topK: number) => void;
  elo: number;
  onEloChange: (elo: number) => void;
  enabled: boolean;
  onEnabledChange: (enabled: boolean) => void;
}

export function ImitatorSettings({
  provider,
  onProviderChange,
  topK,
  onTopKChange,
  elo,
  onEloChange,
  enabled,
  onEnabledChange,
}: ImitatorSettingsProps) {
  return (
    <div className="patch-imitator-settings">
      <div className="patch-imitator-field">
        <span className="patch-analysis-label">Predictor</span>
        <select
          value={provider}
          onChange={(e) => onProviderChange(e.target.value as PredictorProvider)}
        >
          <option value="maia">Maia</option>
          <option value="catie">Catie</option>
        </select>
      </div>
      <div className="patch-imitator-field">
        <span className="patch-analysis-label">Moves</span>
        <select value={topK} onChange={(e) => onTopKChange(Number(e.target.value))}>
          {[3, 5, 8, 10].map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>
      <div className="patch-imitator-field">
        <span className="patch-analysis-label">Elo</span>
        <input
          type="number"
          min={100}
          max={4000}
          step={100}
          value={elo}
          onChange={(e) => onEloChange(Number(e.target.value))}
        />
      </div>
      <div className="patch-imitator-field patch-imitator-toggle">
        <span className="patch-analysis-label">Run</span>
        <label className="patch-toggle">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onEnabledChange(e.target.checked)}
            aria-label="Predictor"
          />
          <span className="patch-toggle-track" />
        </label>
      </div>
    </div>
  );
}
