import React from 'react';
import type { GameRef } from '../types';

interface GameListProps {
  games: GameRef[];
  label: string;
}

export function GameList({ games, label }: GameListProps) {
  if (games.length === 0) return null;

  return (
    <div className="explorer-games">
      <div className="explorer-games__heading">{label}</div>
      {games.map((g, i) => {
        const accentClass =
          g.winner === 'white' ? 'explorer-game--white-wins'
          : g.winner === 'black' ? 'explorer-game--black-wins'
          : 'explorer-game--draw';

        const resultText =
          g.winner === 'white' ? '1–0'
          : g.winner === 'black' ? '0–1'
          : '½–½';

        const date = g.month ?? (g.year != null ? String(g.year) : '');

        return (
          <div
            key={g.id}
            className={`explorer-game ${accentClass}`}
            style={{ animationDelay: `${i * 35}ms`, cursor: 'pointer' }}
            role="button"
            tabIndex={0}
            title="Open game"
            onClick={() => window.open(`/game/${g.id}`, '_blank', 'noopener')}
            onKeyDown={(e) => e.key === 'Enter' && window.open(`/game/${g.id}`, '_blank', 'noopener')}
          >
            <div className="explorer-game__body">
              <div className="explorer-game__row">
                <span className="explorer-game__piece explorer-game__piece--white">♔</span>
                <span className="explorer-game__name">{g.white.name}</span>
                {g.white.rating != null && (
                  <span className="explorer-game__elo">{g.white.rating}</span>
                )}
              </div>
              <div className="explorer-game__row">
                <span className="explorer-game__piece explorer-game__piece--black">♚</span>
                <span className="explorer-game__name">{g.black.name}</span>
                {g.black.rating != null && (
                  <span className="explorer-game__elo">{g.black.rating}</span>
                )}
              </div>
            </div>
            <div className="explorer-game__aside">
              <span className="explorer-game__result">{resultText}</span>
              {date && <span className="explorer-game__date">{date}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
