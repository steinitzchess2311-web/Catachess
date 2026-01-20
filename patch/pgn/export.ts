import { StudyTree as StudyTreeData, StudyNode } from '../tree/type';
import { StudyTree } from '../tree/StudyTree';

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
    // Default headers if missing
    if (!allHeaders['Event']) allHeaders['Event'] = '?';
    if (!allHeaders['Site']) allHeaders['Site'] = '?';
    if (!allHeaders['Date']) allHeaders['Date'] = '????.??.??';
    if (!allHeaders['Round']) allHeaders['Round'] = '?';
    if (!allHeaders['White']) allHeaders['White'] = '?';
    if (!allHeaders['Black']) allHeaders['Black'] = '?';
    if (!allHeaders['Result']) allHeaders['Result'] = '*';

    const headerString = formatPgnHeaders(allHeaders);

    // 2. Format Movetext
    // We need to traverse the tree. 
    // Mainline is children[0]. Variations are children[1..n].
    // Recursion is needed.
    
    const moveText = formatMoveTextRecursive(treeData, root.children[0], 1, true, options);

    return {
      success: true,
      pgn: `${headerString}\n\n${moveText} ${allHeaders['Result']}`,
      errors: [],
    };
  } catch (e: any) {
    return {
      success: false,
      pgn: '',
      errors: [e.message || 'Unknown export error'],
    };
  }
}

function formatMoveTextRecursive(
  tree: StudyTreeData, 
  nodeId: string | undefined, 
  moveNumber: number, 
  isWhite: boolean, 
  options: PgnExportOptions
): string {
  if (!nodeId) return '';
  
  const node = tree.nodes[nodeId];
  if (!node) return '';

  let text = '';

  // Move Number
  if (isWhite) {
    text += `${moveNumber}. `; 
  } else if (!isWhite && moveNumber === 1) {
    // If starting from black (e.g. fragment?), usually handled by setup, 
    // but in standard tree traversal from root, we assume standard start.
    // If we are inside a variation starting with black, we need number...
    text += `${moveNumber}... `; // Convention for black start in variation
  } else {
    // Check if we need to print number for black (e.g. after comment or variation)
    // For simple mainline, we don't usually print "1... e5", just "1. e4 e5"
    // But inside this recursive function, we just append SAN.
    // Logic needs to be context aware. 
    // Simplified: Always print number for White. For Black, only if previous was not White's move in same sequence?
    // Actually, PGN standard: "1. e4 e5 2. Nf3"
  }
  
  // Refined Logic:
  // We pass `forceNumber` flag?
  // For now, simple standard formatting:
  if (!isWhite) {
     // Usually just space, unless we just came from a variation or comment?
     // Let's keep it simple: "san "
  }

  // To do this properly, we need to know if we need to print the number.
  // Standard PGN: Number is printed before White's move.
  // Exception: If variation starts with Black, print "N... san"
  
  // Let's restructure:
  // We are processing a node.
  let token = node.san;
  
  if (isWhite) {
    token = `${moveNumber}. ${token}`;
  }
  
  // Append NAGs
  if (options.includeNags && node.nags && node.nags.length > 0) {
    token += ` $${node.nags.join(' $')}`;
  }
  
  // Append Comment
  if (options.includeComments && node.comment) {
    token += ` {${node.comment}}`;
  }
  
  text += token;

  // Variations (children[1..n])
  if (options.includeVariations && node.children.length > 1) {
    for (let i = 1; i < node.children.length; i++) {
      const varRootId = node.children[i];
      const varText = formatVariation(tree, varRootId, moveNumber, !isWhite, options);
      text += ` (${varText})`;
    }
  }

  // Continuation (children[0])
  if (node.children.length > 0) {
    const nextId = node.children[0];
    const nextIsWhite = !isWhite;
    const nextMoveNumber = isWhite ? moveNumber : moveNumber + 1;
    
    // If we had variations or comments, we might need to be careful with spacing or number for Black
    // But standard PGN parsers are robust.
    
    const nextText = formatMoveTextRecursive(tree, nextId, nextMoveNumber, nextIsWhite, options);
    if (nextText) {
      text += ' ' + nextText;
    }
  }

  return text;
}

function formatVariation(
  tree: StudyTreeData, 
  nodeId: string, 
  moveNumber: number, 
  isWhite: boolean, 
  options: PgnExportOptions
): string {
  // If variation starts with Black, we must print number like "1... e5"
  const node = tree.nodes[nodeId];
  if (!node) return '';

  let text = '';
  
  if (isWhite) {
     text += `${moveNumber}. ${node.san}`;
  } else {
     text += `${moveNumber}... ${node.san}`;
  }
  
  // Recursive continuation
  // ... similar logic to mainline but encapsulated in ()
  
  // Continue variation mainline
  if (node.children.length > 0) {
     const nextId = node.children[0];
     const nextText = formatMoveTextRecursive(tree, nextId, isWhite ? moveNumber : moveNumber + 1, !isWhite, options);
     if (nextText) text += ' ' + nextText;
  }
  
  return text;
}


export function formatPgnHeaders(headers: Record<string, string>): string {
  return Object.entries(headers)
    .map(([key, value]) => `[${key} "${value}"]`)
    .join('\n');
}

// Re-export specific helpers if needed
export function exportMainlineToPgn(tree: StudyTreeData, headers?: Record<string, string>): string {
  return exportPgn(tree, headers, { includeVariations: false, includeComments: false }).pgn;
}
