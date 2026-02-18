import React from 'react';
import type { GameRef } from '../types';

interface GameListProps {
  games: GameRef[];
  label: string;
}

function ResultBadge({ winner }: { winner: GameRef['winner'] }) {
  if (winner === 'white') return <span className="explorer-game__result explorer-game__result--white">1-0</span>;
  if (winner === 'black') return <span className="explorer-game__result explorer-game__result--black">0-1</span>;
  return <span className="explorer-game__result explorer-game__result--draw">½-½</span>;
}

export function GameList({ games, label }: GameListProps) {
  if (games.length === 0) return null;

  return (
    <div className="explorer-games">
      <div className="explorer-games__heading">{label}</div>
      {games.map((g, i) => (
        <div key={g.id} className="explorer-game" style={{ animationDelay: `${i * 35}ms` }}>
          <div className="explorer-game__players">
            <span className="explorer-game__player">
              {g.white.name}
            </span>
            {g.white.rating != null && (
              <span className="explorer-game__elo">{g.white.rating}</span>
            )}
            <span className="explorer-game__vs">vs</span>
            <span className="explorer-game__player">
              {g.black.name}
            </span>
            {g.black.rating != null && (
              <span className="explorer-game__elo">{g.black.rating}</span>
            )}
          </div>
          <div className="explorer-game__meta">
            <ResultBadge winner={g.winner} />
            <span className="explorer-game__date">{g.year ?? g.month ?? ''}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
