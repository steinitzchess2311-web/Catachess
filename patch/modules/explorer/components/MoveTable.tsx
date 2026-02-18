import React from 'react';
import type { MoveEntry } from '../types';
import { totalGames, formatGames } from '../types';
import { WinBar } from './WinBar';

interface MoveTableProps {
  moves: MoveEntry[];
  onMoveClick: (san: string) => void;
}

export function MoveTable({ moves, onMoveClick }: MoveTableProps) {
  if (moves.length === 0) {
    return (
      <div className="explorer-empty">
        No games found for this position.
      </div>
    );
  }

  // Single listener on tbody — event delegation via data-san
  const handleClick = (e: React.MouseEvent<HTMLTableSectionElement>) => {
    const row = (e.target as Element).closest('tr[data-san]');
    const san = row?.getAttribute('data-san');
    if (san) onMoveClick(san);
  };

  return (
    <table className="explorer-moves">
      <colgroup>
        <col className="explorer-moves__col-san" />
        <col className="explorer-moves__col-bar" />
        <col className="explorer-moves__col-games" />
        <col className="explorer-moves__col-elo" />
      </colgroup>
      <thead>
        <tr>
          <th>Move</th>
          <th>Rate</th>
          <th>Games</th>
          <th>Elo</th>
        </tr>
      </thead>
      <tbody onClick={handleClick}>
        {moves.map((m) => (
          <tr
            key={m.uci}
            data-san={m.san}
            className="explorer-moves__row"
            role="button"
            tabIndex={0}
          >
            <td>
              <span className="explorer-moves__san">{m.san}</span>
            </td>
            <td>
              <WinBar white={m.white} draws={m.draws} black={m.black} />
            </td>
            <td>
              <span className="explorer-moves__games">{formatGames(totalGames(m))}</span>
            </td>
            <td>
              <span className="explorer-moves__elo">
                {m.averageRating != null ? m.averageRating : '—'}
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
