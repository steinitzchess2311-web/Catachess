import React from 'react';
import { winRates } from '../types';

interface WinBarProps {
  white: number;
  draws: number;
  black: number;
  /** When set, overrides the bar with player-perspective wins/draws/losses */
  playerStats?: { wins: number; draws: number; losses: number; total: number };
}

export function WinBar({ white, draws, black, playerStats }: WinBarProps) {
  if (playerStats) {
    const { wins, draws: d, losses, total } = playerStats;
    if (total === 0) return <div className="explorer-winbar" title="No games" />;

    const wPct  = (wins   / total) * 100;
    const dPct  = (d      / total) * 100;
    const lPct  = (losses / total) * 100;
    const title = `Win ${wPct.toFixed(1)}% · Draw ${dPct.toFixed(1)}% · Loss ${lPct.toFixed(1)}%`;

    return (
      <div className="explorer-winbar explorer-winbar--player" title={title}>
        {wPct > 0.5 && <div className="explorer-winbar__wins"   style={{ width: `${wPct}%` }} />}
        {dPct > 0.5 && <div className="explorer-winbar__draw"   style={{ width: `${dPct}%` }} />}
        {lPct > 0.5 && <div className="explorer-winbar__losses" style={{ width: `${lPct}%` }} />}
      </div>
    );
  }

  const rates = winRates({ white, draws, black });
  const total = white + draws + black;
  const title = total > 0
    ? `White ${rates.white.toFixed(1)}% · Draw ${rates.draw.toFixed(1)}% · Black ${rates.black.toFixed(1)}%`
    : 'No games';

  return (
    <div className="explorer-winbar" title={title}>
      {rates.white > 0.5 && <div className="explorer-winbar__white" style={{ width: `${rates.white}%` }} />}
      {rates.draw  > 0.5 && <div className="explorer-winbar__draw"  style={{ width: `${rates.draw}%`  }} />}
      {rates.black > 0.5 && <div className="explorer-winbar__black" style={{ width: `${rates.black}%` }} />}
    </div>
  );
}
