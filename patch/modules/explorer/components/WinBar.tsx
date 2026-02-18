import React from 'react';
import { winRates } from '../types';

interface WinBarProps {
  white: number;
  draws: number;
  black: number;
}

export function WinBar({ white, draws, black }: WinBarProps) {
  const rates = winRates({ white, draws, black });
  const total = white + draws + black;
  const title = total > 0
    ? `White ${rates.white.toFixed(1)}% · Draw ${rates.draw.toFixed(1)}% · Black ${rates.black.toFixed(1)}%`
    : 'No games';

  return (
    <div className="explorer-winbar" title={title}>
      {rates.white > 0.5 && (
        <div className="explorer-winbar__white" style={{ width: `${rates.white}%` }} />
      )}
      {rates.draw > 0.5 && (
        <div className="explorer-winbar__draw" style={{ width: `${rates.draw}%` }} />
      )}
      {rates.black > 0.5 && (
        <div className="explorer-winbar__black" style={{ width: `${rates.black}%` }} />
      )}
    </div>
  );
}
