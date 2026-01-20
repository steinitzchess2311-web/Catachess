import { describe, it, expect, vi, beforeEach } from 'vitest';
import { importPgn } from '../../../patch/pgn/import';
import { exportPgn } from '../../../patch/pgn/export';
import { createEmptyTree, StudyTree } from '../../../patch/tree/StudyTree';
import { replaySanPath } from '../../../patch/chessJS/replay';
import { upgradeTree } from '../../../patch/tree/type';

describe('Stage 12 Integration: End-to-End Tree Logic', () => {
  
  it('Import PGN -> Edit Tree -> Export PGN', () => {
    // 1. Import
    const pgn = `[Event "Integration Test"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 *`;
    
    const importResult = importPgn(pgn);
    expect(importResult.success).toBe(true);
    const treeData = importResult.tree!;
    expect(treeData).toBeDefined();
    
    // 2. Edit Tree (Add Move)
    const tree = new StudyTree(treeData);
    const root = tree.getRoot();
    
    // Navigate to end of mainline: 1. e4 e5 2. Nf3 Nc6
    // root -> e4 -> e5 -> Nf3 -> Nc6
    // ids are random, so we must traverse
    let current = root;
    while(current.children.length > 0) {
        current = tree.getNode(current.children[0])!;
    }
    
    expect(current.san).toBe('Nc6');
    
    // Add 3. Bb5
    tree.addMove(current.id, 'Bb5');
    
    // 3. Export
    const exportResult = exportPgn(tree.getData(), { Event: "Integration Test" });
    expect(exportResult.success).toBe(true);
    expect(exportResult.pgn).toContain('3. Bb5');
    expect(exportResult.pgn).toContain('1. e4 e5');
  });

  it('Replay Logic Consistency', () => {
    // Verify that our tree structure produces valid FENs via replay
    const tree = new StudyTree(createEmptyTree());
    const root = tree.getRoot();
    
    const node1 = tree.addMove(root.id, 'e4');
    const node2 = tree.addMove(node1.id, 'e5');
    
    const moves = tree.getPathSan(node2.id);
    expect(moves).toEqual(['e4', 'e5']);
    
    const replay = replaySanPath(moves);
    expect(replay.illegalMoveIndex).toBe(-1);
    expect(replay.finalFen).toContain('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2');
  });

  it('Upgrades legacy tree without version', () => {
    const legacyTree = {
      rootId: 'root',
      nodes: {
        root: {
          id: 'root',
          parentId: null,
          san: '',
          children: [],
          comment: null,
          nags: [],
        },
      },
      meta: { result: null },
    };

    const result = upgradeTree(legacyTree);
    expect(result.migrated).toBe(true);
    expect(result.tree?.version).toBe('v1');
  });
});
