import { Chess } from 'chess.js';
import { STARTING_FEN } from '../chessJS/replay';
import type { StudyTree } from '../tree/type';
import { TREE_SCHEMA_VERSION } from '../tree/type';

/**
 * Converts a space-separated UCI move string (e.g. "e2e4 e7e5 g1f3")
 * into a StudyTree with a linear mainline.
 *
 * Invalid or illegal UCI moves stop the conversion silently — the tree
 * will contain all moves up to (but not including) the first bad move.
 */
export function uciMovesToTree(uciString: string | null, startFen?: string): StudyTree {
  const fen = startFen || STARTING_FEN;
  const board = new Chess(fen);
  const uciMoves = (uciString ?? '').trim().split(/\s+/).filter(Boolean);

  const rootId = 'root';
  const nodes: StudyTree['nodes'] = {
    [rootId]: {
      id: rootId,
      parentId: null,
      san: '',
      children: [],
      comment: null,
      nags: [],
    },
  };

  let parentId = rootId;
  for (let i = 0; i < uciMoves.length; i++) {
    const uci = uciMoves[i];
    const from = uci.slice(0, 2);
    const to = uci.slice(2, 4);
    const promotion = uci.length > 4 ? uci[4] : undefined;

    let moveResult;
    try {
      moveResult = board.move({ from, to, promotion });
    } catch {
      break;
    }
    if (!moveResult) break;

    const nodeId = `n${i}`;
    nodes[nodeId] = {
      id: nodeId,
      parentId,
      san: moveResult.san,
      children: [],
      comment: null,
      nags: [],
    };
    nodes[parentId].children.push(nodeId);
    parentId = nodeId;
  }

  return {
    version: TREE_SCHEMA_VERSION,
    rootId,
    nodes,
    meta: { result: null },
  };
}
