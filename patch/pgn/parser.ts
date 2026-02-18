/**
 * Recursive PGN Parser
 *
 * Replaces chess.js loadPgn() with a full recursive-descent parser that:
 * - Preserves all variations (sub-lines)
 * - Parses move annotations ([%csl], [%cal], [%clk])
 * - Validates each SAN via chess.js board.move()
 * - Applies a "best-effort" strategy: invalid moves are skipped, not fatal
 * - Stops building after MAX_NODES to prevent memory issues
 *
 * Architecture:
 *   tokenize(pgn) → Token[]
 *   buildTree(tokens, startFen) → StudyTree + errors[]
 */

import { Chess } from 'chess.js';
import type { StudyTree as StudyTreeData, StudyNode, Shape } from '../tree/type';
import { TREE_SCHEMA_VERSION } from '../tree/type';
import { createEmptyTree } from '../tree/StudyTree';
import { parseComment } from './comment-parser';

// ---------------------------------------------------------------------------
// Token types
// ---------------------------------------------------------------------------

type Token =
  | { type: 'header'; key: string; value: string }
  | { type: 'move_number'; num: number; isBlack: boolean }
  | { type: 'san'; value: string }
  | { type: 'comment'; value: string }
  | { type: 'nag'; value: number }
  | { type: 'variation_start' }
  | { type: 'variation_end' }
  | { type: 'result'; value: string };

// ---------------------------------------------------------------------------
// Tokenizer
// ---------------------------------------------------------------------------

const ANNOTATION_NAG: Record<string, number> = {
  '!': 1,
  '?': 2,
  '!!': 3,
  '??': 4,
  '!?': 5,
  '?!': 6,
};

export function tokenize(pgn: string): Token[] {
  const tokens: Token[] = [];
  const n = pgn.length;
  let i = 0;

  while (i < n) {
    const ch = pgn[i];

    // Whitespace
    if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') {
      i++;
      continue;
    }

    // Header [Key "Value"]
    if (ch === '[') {
      let j = i + 1;
      // Headers can span lines; find matching ]
      while (j < n && pgn[j] !== ']') j++;
      const content = pgn.slice(i + 1, j);
      const m = content.match(/^(\w+)\s+"((?:[^"\\]|\\.)*)"$/);
      if (m) {
        tokens.push({ type: 'header', key: m[1], value: m[2].replace(/\\"/g, '"') });
      }
      i = j + 1;
      continue;
    }

    // Comment { ... }
    if (ch === '{') {
      let j = i + 1;
      while (j < n && pgn[j] !== '}') j++;
      tokens.push({ type: 'comment', value: pgn.slice(i + 1, j) });
      i = j + 1;
      continue;
    }

    // Line comment ; ...  (skip to end of line)
    if (ch === ';') {
      while (i < n && pgn[i] !== '\n') i++;
      continue;
    }

    // Variation markers
    if (ch === '(') { tokens.push({ type: 'variation_start' }); i++; continue; }
    if (ch === ')') { tokens.push({ type: 'variation_end' }); i++; continue; }

    // NAG  $N
    if (ch === '$') {
      i++;
      let num = '';
      while (i < n && pgn[i] >= '0' && pgn[i] <= '9') num += pgn[i++];
      if (num) tokens.push({ type: 'nag', value: parseInt(num, 10) });
      continue;
    }

    // Result *
    if (ch === '*') { tokens.push({ type: 'result', value: '*' }); i++; continue; }

    // Informal annotation glyphs  ! ? !! ?? !? ?!
    if (ch === '!' || ch === '?') {
      const next = pgn[i + 1];
      let sym = ch;
      if (next === '!' || next === '?') { sym += next; i += 2; } else { i++; }
      const nagVal = ANNOTATION_NAG[sym];
      if (nagVal !== undefined) tokens.push({ type: 'nag', value: nagVal });
      continue;
    }

    // Digits: move number or result (1-0, 0-1, 1/2-1/2)
    if (ch >= '0' && ch <= '9') {
      let j = i;
      while (j < n && pgn[j] >= '0' && pgn[j] <= '9') j++;
      const numStr = pgn.slice(i, j);

      // 1/2-1/2
      if (pgn[j] === '/') {
        const candidate = pgn.slice(i, i + 9);
        if (candidate === '1/2-1/2') {
          tokens.push({ type: 'result', value: '1/2-1/2' });
          i += 9;
          continue;
        }
      }

      // 1-0 or 0-1
      if (pgn[j] === '-' && j + 1 < n) {
        let k = j + 1;
        while (k < n && pgn[k] >= '0' && pgn[k] <= '9') k++;
        const candidate = pgn.slice(i, k);
        if (candidate === '1-0' || candidate === '0-1') {
          tokens.push({ type: 'result', value: candidate });
          i = k;
          continue;
        }
      }

      // Move number N. or N...
      if (j < n && pgn[j] === '.') {
        let k = j;
        while (k < n && pgn[k] === '.') k++;
        const isBlack = k - j >= 3;
        tokens.push({ type: 'move_number', num: parseInt(numStr, 10), isBlack });
        i = k;
        continue;
      }

      // Unrecognized number sequence, skip
      i = j;
      continue;
    }

    // SAN / word (starts with letter)
    if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
      let j = i;
      // SAN chars: letters, digits, hyphen (for O-O), +, #, =
      while (
        j < n &&
        (
          (pgn[j] >= 'a' && pgn[j] <= 'z') ||
          (pgn[j] >= 'A' && pgn[j] <= 'Z') ||
          (pgn[j] >= '0' && pgn[j] <= '9') ||
          pgn[j] === '-' ||
          pgn[j] === '+' ||
          pgn[j] === '#' ||
          pgn[j] === '='
        )
      ) j++;
      const word = pgn.slice(i, j);
      tokens.push({ type: 'san', value: word });
      i = j;
      continue;
    }

    // Unknown character – skip
    i++;
  }

  return tokens;
}

// ---------------------------------------------------------------------------
// Tree builder
// ---------------------------------------------------------------------------

const MAX_NODES = 10_000;

function generateId(): string {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
}

export interface ParsedGame {
  headers: Record<string, string>;
  tree: StudyTreeData;
  /** From [FEN "..."] header, if present */
  startingFen: string | undefined;
  errors: string[];
}

export function parsePgn(pgn: string): ParsedGame {
  const tokens = tokenize(pgn);
  const headers: Record<string, string> = {};
  const errors: string[] = [];

  // --- Phase 1: Collect headers ---
  let ti = 0;
  while (ti < tokens.length && tokens[ti].type === 'header') {
    const tok = tokens[ti] as { type: 'header'; key: string; value: string };
    headers[tok.key] = tok.value;
    ti++;
  }

  const startingFen = headers['FEN'];
  const tree = createEmptyTree();

  // --- Phase 2: Build tree from move tokens ---
  const STARTING = startingFen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  let nodeCount = Object.keys(tree.nodes).length;

  // Current insertion point: node ID where the next SAN will be appended
  let currentNodeId = tree.rootId;

  /**
   * nodeFen tracks the board FEN at each node position (the FEN BEFORE the
   * node's own move was played, i.e. the board state that the node was played
   * from).  This avoids relying on Chess.undo() across FEN-constructed boards.
   *
   * root → STARTING fen
   * any child node → fen of the board the child's move was played from
   *
   * We use "parent FEN" logic: to play the next move, we need the FEN at
   * currentNodeId (which is the result of all moves up to that node).
   * We store the FEN AFTER each node's move so we can reconstruct any parent.
   */
  const nodeFen = new Map<string, string>();
  nodeFen.set(tree.rootId, STARTING);

  // Stack of return-points for variations
  // Each '(' saves the current (nodeId, fen) to restore on matching ')'
  type Frame = { nodeId: string; fen: string };
  const frameStack: Frame[] = [];

  for (let ti2 = ti; ti2 < tokens.length; ti2++) {
    const tok = tokens[ti2];

    if (nodeCount >= MAX_NODES) {
      errors.push(`Node limit (${MAX_NODES}) reached; remaining moves truncated`);
      break;
    }

    switch (tok.type) {
      case 'header':
        // Headers should all be at the start; ignore any embedded ones
        break;

      case 'move_number':
        // Move numbers are redundant; skip
        break;

      case 'san': {
        // Get the board at the current node (the position we'll play from)
        const parentFen = nodeFen.get(currentNodeId);
        if (!parentFen) {
          errors.push(`Missing FEN for node ${currentNodeId}; skipping "${tok.value}"`);
          break;
        }

        // Create a fresh board from the stored FEN – avoids undo() issues
        const board = new Chess(parentFen);
        let moveResult: ReturnType<Chess['move']> | null = null;
        try {
          moveResult = board.move(tok.value);
        } catch {
          moveResult = null;
        }

        if (!moveResult) {
          // Best-effort: skip illegal / unrecognized moves
          errors.push(`Skipped illegal SAN: "${tok.value}"`);
          break;
        }

        const newId = generateId();
        const newNode: StudyNode = {
          id: newId,
          parentId: currentNodeId,
          san: moveResult.san,
          children: [],
          comment: null,
          nags: [],
        };

        tree.nodes[newId] = newNode;
        tree.nodes[currentNodeId].children.push(newId);
        // Store the FEN AFTER this move so child nodes can use it
        nodeFen.set(newId, board.fen());
        currentNodeId = newId;
        nodeCount++;
        break;
      }

      case 'comment': {
        // Attach to the CURRENT node (the last played move)
        if (currentNodeId !== tree.rootId) {
          const parsed = parseComment(tok.value);
          const node = tree.nodes[currentNodeId];
          if (parsed.text) {
            node.comment = node.comment
              ? `${node.comment} ${parsed.text}`
              : parsed.text;
          }
          if (parsed.shapes.length > 0) {
            node.shapes = [...(node.shapes ?? []), ...parsed.shapes];
          }
          if (parsed.clock != null) {
            node.clock = parsed.clock;
          }
        }
        break;
      }

      case 'nag': {
        if (currentNodeId !== tree.rootId) {
          const node = tree.nodes[currentNodeId];
          if (!node.nags.includes(tok.value)) {
            node.nags = [...node.nags, tok.value];
          }
        }
        break;
      }

      case 'variation_start': {
        // Save the current state (after last move) and rewind to parent
        const currentNode = tree.nodes[currentNodeId];
        if (!currentNode || currentNode.parentId === null) {
          // At root – can't rewind further; push a no-op frame
          frameStack.push({ nodeId: currentNodeId, fen: nodeFen.get(currentNodeId) ?? STARTING });
          break;
        }

        // Save return point (the state AFTER the current move)
        const currentFen = nodeFen.get(currentNodeId) ?? STARTING;
        frameStack.push({ nodeId: currentNodeId, fen: currentFen });

        // Rewind to parent: the variation branches from the parent's position.
        // The parent's "board state" is stored as nodeFen[parent] which is the FEN
        // AFTER the parent's own move (i.e. the position the current node was played from).
        // So the parent's board = nodeFen[parent].
        const parentId = currentNode.parentId;
        currentNodeId = parentId;
        // (nodeFen[parentId] is already set; we just update currentNodeId)
        break;
      }

      case 'variation_end': {
        if (frameStack.length > 0) {
          const frame = frameStack.pop()!;
          currentNodeId = frame.nodeId;
          // nodeFen[frame.nodeId] is already set; no board reconstruction needed
        }
        break;
      }

      case 'result': {
        if (!tree.meta.result && tok.value !== '*') {
          tree.meta.result = tok.value;
        }
        break;
      }
    }
  }

  // Use Result header if not found in movetext
  if (!tree.meta.result && headers['Result'] && headers['Result'] !== '*') {
    tree.meta.result = headers['Result'];
  }

  return { headers, tree, startingFen, errors };
}
