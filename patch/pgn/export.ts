import { StudyTree as StudyTreeData, StudyNode } from '../tree/type';
import { StudyTree } from '../tree/StudyTree';
import { serializeCommentParts } from './comment-parser';

export interface PgnExportOptions {
  includeComments?: boolean;
  includeNags?: boolean;
  includeVariations?: boolean;
}

export interface PgnExportResult {
  success: boolean;
  pgn: string;
  errors: string[];
}

/**
 * Exports a StudyTree to a PGN string.
 * Uses caller-provided headers and tree.meta.result.
 * Shapes and clock are serialized back into PGN comments ([%csl], [%cal], [%clk]).
 */
export function exportPgn(
  treeData: StudyTreeData,
  headers: Record<string, string> = {},
  options: PgnExportOptions = {}
): PgnExportResult {
  try {
    const treeOps = new StudyTree(treeData);
    const root = treeOps.getRoot();

    // 1. Format Headers
    const allHeaders = { ...headers };
    if (treeData.meta.result && !allHeaders['Result']) {
      allHeaders['Result'] = treeData.meta.result;
    }
    if (!allHeaders['Event']) allHeaders['Event'] = '?';
    if (!allHeaders['Site']) allHeaders['Site'] = '?';
    if (!allHeaders['Date']) allHeaders['Date'] = '????.??.??';
    if (!allHeaders['Round']) allHeaders['Round'] = '?';
    if (!allHeaders['White']) allHeaders['White'] = '?';
    if (!allHeaders['Black']) allHeaders['Black'] = '?';
    if (!allHeaders['Result']) allHeaders['Result'] = '*';

    const headerString = formatPgnHeaders(allHeaders);

    // 2. Format Movetext
    const moveText = formatMoveTextRecursive(
      treeData,
      root.children[0],
      1,
      true,
      options
    );

    return {
      success: true,
      pgn: `${headerString}\n\n${moveText} ${allHeaders['Result']}`.trimEnd(),
      errors: [],
    };
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Unknown export error';
    return { success: false, pgn: '', errors: [msg] };
  }
}

// ---------------------------------------------------------------------------
// Comment serialization (v2 round-trip)
// ---------------------------------------------------------------------------

/**
 * Produce the PGN comment token for a node, including shapes, clock, and text.
 * Returns an empty string when the node has nothing to annotate.
 */
function serializeNodeComment(node: StudyNode, opts: PgnExportOptions): string {
  if (!opts.includeComments) return '';

  const parts = serializeCommentParts(node.shapes, node.clock, node.comment);
  return parts ? `{ ${parts} }` : '';
}

// ---------------------------------------------------------------------------
// Recursive move-text formatter
// ---------------------------------------------------------------------------

function formatMoveTextRecursive(
  tree: StudyTreeData,
  nodeId: string | undefined,
  moveNumber: number,
  isWhite: boolean,
  options: PgnExportOptions,
  /** True when we need to print "N..." even for the first black token */
  forceNumber = false
): string {
  if (!nodeId) return '';

  const node = tree.nodes[nodeId];
  if (!node) return '';

  let text = '';

  // Move number prefix
  if (isWhite) {
    text += `${moveNumber}. `;
  } else if (forceNumber) {
    text += `${moveNumber}... `;
  }

  text += node.san;

  // NAGs
  if (options.includeNags && node.nags && node.nags.length > 0) {
    text += ` $${node.nags.join(' $')}`;
  }

  // Comment (includes shapes + clock in v2)
  const comment = serializeNodeComment(node, options);
  if (comment) text += ` ${comment}`;

  // Variations (children[1..n])
  if (options.includeVariations && node.children.length > 1) {
    for (let i = 1; i < node.children.length; i++) {
      const varId = node.children[i];
      const varText = formatVariation(tree, varId, moveNumber, isWhite, options);
      if (varText) text += ` (${varText})`;
    }
  }

  // Continuation (children[0])
  if (node.children.length > 0) {
    const nextId = node.children[0];
    const nextIsWhite = !isWhite;
    const nextMoveNumber = isWhite ? moveNumber : moveNumber + 1;

    // After variations or comments, black's next move needs a number prefix
    const needForceNumber =
      !isWhite === false // nextIsWhite === false means black is next
        ? false
        : (options.includeVariations && node.children.length > 1) ||
          comment.length > 0;

    const nextText = formatMoveTextRecursive(
      tree,
      nextId,
      nextMoveNumber,
      nextIsWhite,
      options,
      needForceNumber
    );
    if (nextText) text += ' ' + nextText;
  }

  return text;
}

function formatVariation(
  tree: StudyTreeData,
  nodeId: string,
  moveNumber: number,
  parentIsWhite: boolean,
  options: PgnExportOptions
): string {
  const node = tree.nodes[nodeId];
  if (!node) return '';

  // Variation starts from the SAME side as the parent's last move was
  // (the variation replaces that last move), so colour is the same as parent.
  // parentIsWhite = colour of the node that starts this variation.
  const varIsWhite = parentIsWhite;

  // For black variations we always need "N..."
  const forceNumber = !varIsWhite;

  let text = '';
  if (varIsWhite) {
    text += `${moveNumber}. ${node.san}`;
  } else {
    text += `${moveNumber}... ${node.san}`;
  }

  if (options.includeNags && node.nags?.length) {
    text += ` $${node.nags.join(' $')}`;
  }

  const comment = serializeNodeComment(node, options);
  if (comment) text += ` ${comment}`;

  if (node.children.length > 0) {
    const nextId = node.children[0];
    const nextIsWhite = !varIsWhite;
    const nextMoveNumber = varIsWhite ? moveNumber : moveNumber + 1;

    const needForce =
      nextIsWhite === false &&
      ((options.includeVariations && node.children.length > 1) || comment.length > 0);

    const rest = formatMoveTextRecursive(
      tree,
      nextId,
      nextMoveNumber,
      nextIsWhite,
      options,
      needForce
    );
    if (rest) text += ' ' + rest;
  }

  return text;
}

// ---------------------------------------------------------------------------
// Public helpers
// ---------------------------------------------------------------------------

export function formatPgnHeaders(headers: Record<string, string>): string {
  return Object.entries(headers)
    .map(([key, value]) => `[${key} "${value}"]`)
    .join('\n');
}

export function exportMainlineToPgn(
  tree: StudyTreeData,
  headers?: Record<string, string>
): string {
  return exportPgn(tree, headers, {
    includeVariations: false,
    includeComments: false,
  }).pgn;
}
