/**
 * Quick functional test for the PGN parser logic.
 * Runs in Node.js using chess.js CJS build directly.
 */
import { createRequire } from 'module';
import { readFileSync } from 'fs';

const require = createRequire(import.meta.url);
const { Chess } = require('./frontend/web/node_modules/chess.js/dist/cjs/chess.js');

// ─── Tokenizer ─────────────────────────────────────────────────────────────

const ANNOTATION_NAG = { '!': 1, '?': 2, '!!': 3, '??': 4, '!?': 5, '?!': 6 };

function tokenize(pgn) {
  const tokens = [];
  const n = pgn.length;
  let i = 0;
  while (i < n) {
    const ch = pgn[i];
    if (ch === ' ' || ch === '\t' || ch === '\r' || ch === '\n') { i++; continue; }
    if (ch === '[') {
      let j = i + 1; while (j < n && pgn[j] !== ']') j++;
      const content = pgn.slice(i + 1, j);
      const m = content.match(/^(\w+)\s+"((?:[^"\\]|\\.)*)"$/);
      if (m) tokens.push({ type: 'header', key: m[1], value: m[2].replace(/\\"/g, '"') });
      i = j + 1; continue;
    }
    if (ch === '{') {
      let j = i + 1; while (j < n && pgn[j] !== '}') j++;
      tokens.push({ type: 'comment', value: pgn.slice(i + 1, j) });
      i = j + 1; continue;
    }
    if (ch === ';') { while (i < n && pgn[i] !== '\n') i++; continue; }
    if (ch === '(') { tokens.push({ type: 'variation_start' }); i++; continue; }
    if (ch === ')') { tokens.push({ type: 'variation_end' }); i++; continue; }
    if (ch === '$') {
      i++; let num = '';
      while (i < n && pgn[i] >= '0' && pgn[i] <= '9') num += pgn[i++];
      if (num) tokens.push({ type: 'nag', value: parseInt(num, 10) });
      continue;
    }
    if (ch === '*') { tokens.push({ type: 'result', value: '*' }); i++; continue; }
    if (ch === '!' || ch === '?') {
      const next = pgn[i + 1];
      let sym = ch;
      if (next === '!' || next === '?') { sym += next; i += 2; } else { i++; }
      const nagVal = ANNOTATION_NAG[sym];
      if (nagVal !== undefined) tokens.push({ type: 'nag', value: nagVal });
      continue;
    }
    if (ch >= '0' && ch <= '9') {
      let j = i; while (j < n && pgn[j] >= '0' && pgn[j] <= '9') j++;
      const numStr = pgn.slice(i, j);
      if (pgn[j] === '/') {
        const c = pgn.slice(i, i + 9);
        if (c === '1/2-1/2') { tokens.push({ type: 'result', value: '1/2-1/2' }); i += 9; continue; }
      }
      if (pgn[j] === '-' && j + 1 < n) {
        let k = j + 1; while (k < n && pgn[k] >= '0' && pgn[k] <= '9') k++;
        const c = pgn.slice(i, k);
        if (c === '1-0' || c === '0-1') { tokens.push({ type: 'result', value: c }); i = k; continue; }
      }
      if (j < n && pgn[j] === '.') {
        let k = j; while (k < n && pgn[k] === '.') k++;
        tokens.push({ type: 'move_number', num: parseInt(numStr, 10), isBlack: k - j >= 3 });
        i = k; continue;
      }
      i = j; continue;
    }
    if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
      let j = i;
      while (j < n && ((pgn[j] >= 'a' && pgn[j] <= 'z') || (pgn[j] >= 'A' && pgn[j] <= 'Z') ||
             (pgn[j] >= '0' && pgn[j] <= '9') || pgn[j] === '-' || pgn[j] === '+' || pgn[j] === '#' || pgn[j] === '=')) j++;
      tokens.push({ type: 'san', value: pgn.slice(i, j) });
      i = j; continue;
    }
    i++;
  }
  return tokens;
}

// ─── Parser (using nodeFen map to avoid undo() issues) ─────────────────────

function generateId() {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
}

function parsePgn(pgn) {
  const tokens = tokenize(pgn);
  const headers = {};
  const errors = [];
  const nodes = {};
  const rootId = 'root';
  nodes[rootId] = { id: rootId, parentId: null, san: '', children: [], comment: null, nags: [], shapes: [] };

  let ti = 0;
  while (ti < tokens.length && tokens[ti].type === 'header') {
    headers[tokens[ti].key] = tokens[ti].value;
    ti++;
  }

  const startingFen = headers['FEN'];
  const STARTING = startingFen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  const nodeFen = new Map();
  nodeFen.set(rootId, STARTING);

  let currentNodeId = rootId;
  const frameStack = [];
  let nodeCount = 1;

  for (let ti2 = ti; ti2 < tokens.length; ti2++) {
    const tok = tokens[ti2];
    if (nodeCount >= 10000) { errors.push('Node limit reached'); break; }

    if (tok.type === 'san') {
      const parentFen = nodeFen.get(currentNodeId);
      if (!parentFen) { errors.push(`No FEN for node ${currentNodeId}`); continue; }
      const board = new Chess(parentFen);
      let moveResult = null;
      try { moveResult = board.move(tok.value); } catch {}
      if (!moveResult) { errors.push(`Skipped: "${tok.value}"`); continue; }
      const newId = generateId();
      nodes[newId] = { id: newId, parentId: currentNodeId, san: moveResult.san, children: [], comment: null, nags: [], shapes: [] };
      nodes[currentNodeId].children.push(newId);
      nodeFen.set(newId, board.fen());
      currentNodeId = newId;
      nodeCount++;
    } else if (tok.type === 'comment') {
      // parse [%csl] and [%cal] shapes
      const text = tok.value.trim();
      const cslMatch = text.match(/\[%csl ([^\]]+)\]/);
      const calMatch = text.match(/\[%cal ([^\]]+)\]/);
      if (currentNodeId !== rootId) {
        const node = nodes[currentNodeId];
        if (cslMatch) {
          for (const part of cslMatch[1].split(',')) {
            const s = part.trim();
            if (s.length >= 3) node.shapes.push({ type: 'circle', color: s[0], square: s.slice(1) });
          }
        }
        if (calMatch) {
          for (const part of calMatch[1].split(',')) {
            const s = part.trim();
            if (s.length >= 5) node.shapes.push({ type: 'arrow', color: s[0], from: s.slice(1,3), to: s.slice(3,5) });
          }
        }
        const plain = text.replace(/\[%\w+ [^\]]*\]/g, '').trim();
        if (plain) node.comment = plain.slice(0, 100);
      }
    } else if (tok.type === 'nag') {
      if (currentNodeId !== rootId) nodes[currentNodeId].nags.push(tok.value);
    } else if (tok.type === 'variation_start') {
      const currentNode = nodes[currentNodeId];
      if (!currentNode || currentNode.parentId === null) {
        frameStack.push({ nodeId: currentNodeId });
      } else {
        frameStack.push({ nodeId: currentNodeId });
        currentNodeId = currentNode.parentId;
      }
    } else if (tok.type === 'variation_end') {
      if (frameStack.length > 0) {
        currentNodeId = frameStack.pop().nodeId;
      }
    }
  }

  return { headers, nodes, rootId, errors, nodeCount };
}

function splitMultiPgn(content, max = 64) {
  return content.replace(/\r/g, '').split(/\n\n(?=\[)/).filter(s => s.trim().length > 0).slice(0, max);
}

// ─── Tests ──────────────────────────────────────────────────────────────────

console.log('=== Test 1: Basic variation ===');
{
  const pgn = '1. e4 (1. d4 d5) 1... e5 2. Nf3 *';
  const r = parsePgn(pgn);
  const rootChildren = r.nodes[r.rootId].children.length;
  console.log(`Root children: ${rootChildren} (expected 2)`);  // e4 and d4
  const e4Id = r.nodes[r.rootId].children[0];
  const e4Node = r.nodes[e4Id];
  console.log(`First child: ${e4Node.san} (expected e4)`);
  const d4Id = r.nodes[r.rootId].children[1];
  const d4Node = r.nodes[d4Id];
  console.log(`Second child: ${d4Node?.san} (expected d4)`);
  const e5Id = e4Node.children[0];
  const e5Node = r.nodes[e5Id];
  console.log(`After e4: ${e5Node?.san} (expected e5)`);
  if (rootChildren === 2 && e4Node.san === 'e4' && d4Node?.san === 'd4' && e5Node?.san === 'e5') {
    console.log('✓ Basic variation test PASSED');
  } else {
    console.log('✗ Basic variation test FAILED');
  }
  if (r.errors.length) console.log('  Errors:', r.errors);
}

console.log('\n=== Test 2: Nested variations ===');
{
  const pgn = '1. e4 (1. d4 d5 (1... c5)) 1... e5 *';
  const r = parsePgn(pgn);
  const rootChildren = r.nodes[r.rootId].children.length;
  const d4Id = r.nodes[r.rootId].children[1];
  const d4Node = r.nodes[d4Id];
  const d4Children = d4Node?.children?.length ?? 0;
  console.log(`Root children: ${rootChildren} (expected 2)`);
  console.log(`d4 children: ${d4Children} (expected 2: d5 and c5)`);
  if (rootChildren === 2 && d4Children === 2) {
    console.log('✓ Nested variation test PASSED');
  } else {
    console.log('✗ Nested variation test FAILED');
    console.log('  d4 children:', d4Node?.children?.map(id => r.nodes[id]?.san));
  }
  if (r.errors.length) console.log('  Errors:', r.errors);
}

console.log('\n=== Test 3: Comment with shapes ===');
{
  const pgn = '1. e4 { [%csl Ge4,Rd5] [%cal Ge2e4] Good square! } e5 *';
  const r = parsePgn(pgn);
  const e4Id = r.nodes[r.rootId].children[0];
  const e4Node = r.nodes[e4Id];
  console.log(`Shapes: ${JSON.stringify(e4Node?.shapes)}`);
  console.log(`Comment: ${e4Node?.comment}`);
  if ((e4Node?.shapes?.length ?? 0) >= 3 && e4Node?.comment) {
    console.log('✓ Comment/shapes test PASSED');
  } else {
    console.log('✗ Comment/shapes test FAILED');
  }
}

console.log('\n=== Test 4: Multi-game split ===');
{
  const multi = '[White "A"]\n[Black "B"]\n\n1. e4 e5 *\n\n[White "C"]\n[Black "D"]\n\n1. d4 d5 *';
  const games = splitMultiPgn(multi);
  console.log(`Games found: ${games.length} (expected 2)`);
  if (games.length === 2) console.log('✓ Multi-game split PASSED');
  else console.log('✗ Multi-game split FAILED');
}

console.log('\n=== Test 5: Real PGN file (Philidor) ===');
{
  const content = readFileSync('/Users/alex_1/Desktop/Philidor for Black.pgn', 'utf-8');
  console.log(`File size: ${content.length} chars`);
  const games = splitMultiPgn(content, 100);
  console.log(`Games found: ${games.length}`);

  let totalNodes = 0, totalErrors = 0;
  for (let i = 0; i < Math.min(5, games.length); i++) {
    const result = parsePgn(games[i]);
    totalNodes += result.nodeCount;
    totalErrors += result.errors.length;
    const chapter = result.headers['ChapterName'] ?? result.headers['White'] ?? '?';
    let variationForks = 0;
    for (const node of Object.values(result.nodes)) {
      if (node.children.length > 1) variationForks++;
    }
    let nodesWithShapes = 0;
    for (const node of Object.values(result.nodes)) {
      if (node.shapes?.length) nodesWithShapes++;
    }
    console.log(`  Game ${i+1}: "${chapter}" → ${result.nodeCount} nodes, ${variationForks} forks, ${nodesWithShapes} nodes with shapes, ${result.errors.length} errors`);
  }
  console.log(`\n  Total: ${totalNodes} nodes, ${totalErrors} errors`);
  if (totalErrors === 0) {
    console.log('✓ Real PGN test PASSED (no errors)');
  } else {
    console.log(`⚠ Real PGN test: ${totalErrors} errors (may be acceptable)`);
  }
}

console.log('\n=== All tests done ===');
