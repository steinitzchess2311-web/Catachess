// ============================================================
// MoveList — 走法列表（棋谱）
//
// 支持点击回看历史局面（只读，不影响对局）
// 格式：1. e4 e5  2. Nf3 Nc6  ...
// ============================================================

import React, { useEffect, useRef } from 'react';

interface MoveListProps {
  moves: string[];                   // SAN 走法数组
  /** 当前查看的走法索引（null = 初始局面）*/
  viewIndex: number | null;
  onSelectMove: (index: number | null) => void;
}

/** 将线性 SAN 数组转为回合行结构 */
function buildRows(moves: string[]): Array<{ num: number; white: string; black?: string; wIdx: number; bIdx?: number }> {
  const rows: Array<{ num: number; white: string; black?: string; wIdx: number; bIdx?: number }> = [];
  for (let i = 0; i < moves.length; i += 2) {
    rows.push({
      num: Math.floor(i / 2) + 1,
      white: moves[i],
      black: moves[i + 1],
      wIdx: i,
      bIdx: i + 1 < moves.length ? i + 1 : undefined,
    });
  }
  return rows;
}

export function MoveList({ moves, viewIndex, onSelectMove }: MoveListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const isViewingHistory = viewIndex !== null && viewIndex < moves.length - 1;

  // 只有在跟随最新走法时才自动滚到底部
  useEffect(() => {
    if (!isViewingHistory) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [moves.length, isViewingHistory]);

  if (moves.length === 0) {
    return (
      <div className="ug-movelist ug-movelist--empty">
        <span>Game in progress...</span>
      </div>
    );
  }

  const rows = buildRows(moves);

  return (
    <div className="ug-movelist">
      <table className="ug-movelist__table">
        <tbody>
          {rows.map((row) => (
            <tr key={row.num} className="ug-movelist__row">
              {/* 回合数 */}
              <td className="ug-movelist__num">{row.num}.</td>

              {/* 白方走法 */}
              <td
                className={[
                  'ug-movelist__move',
                  viewIndex === row.wIdx ? 'ug-movelist__move--active' : '',
                ].join(' ')}
                onClick={() => onSelectMove(row.wIdx)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && onSelectMove(row.wIdx)}
              >
                {row.white}
              </td>

              {/* 黑方走法（可能没有，最后半步）*/}
              <td
                className={[
                  'ug-movelist__move',
                  row.bIdx !== undefined && viewIndex === row.bIdx
                    ? 'ug-movelist__move--active'
                    : '',
                  row.bIdx === undefined ? 'ug-movelist__move--empty' : '',
                ].join(' ')}
                onClick={() => row.bIdx !== undefined && onSelectMove(row.bIdx)}
                role={row.bIdx !== undefined ? 'button' : undefined}
                tabIndex={row.bIdx !== undefined ? 0 : undefined}
                onKeyDown={(e) =>
                  e.key === 'Enter' && row.bIdx !== undefined && onSelectMove(row.bIdx)
                }
              >
                {row.black ?? ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 回看历史时显示提示条 */}
      {isViewingHistory && (
        <button
          type="button"
          className="ug-movelist__back-to-live"
          onClick={() => onSelectMove(null)}
        >
          ↓ Back to live position
        </button>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
