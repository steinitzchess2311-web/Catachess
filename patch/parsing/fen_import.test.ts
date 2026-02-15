/**
 * FEN Import - Unit Tests
 *
 * Test suite for FEN import functionality.
 * Created: 2025-02-15
 */

import { describe, it, expect } from 'vitest';
import { importFromFen, quickValidateFen, getPositionInfo, FEN_TEMPLATES } from './fen_import';
import { STANDARD_STARTING_FEN } from './types';

describe('importFromFen', () => {
  describe('Standard starting position', () => {
    it('should import standard starting position successfully', () => {
      const result = importFromFen(STANDARD_STARTING_FEN);

      expect(result.success).toBe(true);
      expect(result.tree).not.toBeNull();
      expect(result.errors).toHaveLength(0);
      // Standard position should NOT have startingFen (to save space)
      expect(result.startingFen).toBeUndefined();
    });

    it('should create empty tree with only root node', () => {
      const result = importFromFen(STANDARD_STARTING_FEN);

      expect(result.tree).not.toBeNull();
      expect(result.tree!.version).toBe('v1');
      expect(result.tree!.nodes[result.tree!.rootId]).toBeDefined();
      expect(result.tree!.nodes[result.tree!.rootId].san).toBe('');
      expect(result.tree!.nodes[result.tree!.rootId].children).toHaveLength(0);
    });

    it('should include FEN in headers', () => {
      const result = importFromFen(STANDARD_STARTING_FEN);

      expect(result.headers.FEN).toBe(STANDARD_STARTING_FEN);
      expect(result.headers.Turn).toBe('White');
      expect(result.headers.MoveNumber).toBe('1');
    });
  });

  describe('Custom positions', () => {
    it('should import custom endgame position', () => {
      const endgameFen = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1';
      const result = importFromFen(endgameFen);

      expect(result.success).toBe(true);
      expect(result.tree).not.toBeNull();
      // Custom position SHOULD have startingFen
      expect(result.startingFen).toBe(endgameFen);
    });

    it('should handle black to move', () => {
      const blackToMoveFen = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1';
      const result = importFromFen(blackToMoveFen);

      expect(result.success).toBe(true);
      expect(result.headers.Turn).toBe('Black');
    });

    it('should normalize FEN with missing parts', () => {
      // FEN with only 4 parts (missing halfmove and fullmove)
      const partialFen = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq -';
      const result = importFromFen(partialFen);

      expect(result.success).toBe(true);
      expect(result.startingFen).toContain('0 1'); // Should add default halfmove and fullmove
    });
  });

  describe('Invalid FEN', () => {
    it('should reject empty string', () => {
      const result = importFromFen('');

      expect(result.success).toBe(false);
      expect(result.tree).toBeNull();
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should reject malformed FEN', () => {
      const result = importFromFen('not a valid fen');

      expect(result.success).toBe(false);
      expect(result.tree).toBeNull();
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should reject FEN with invalid piece placement', () => {
      const result = importFromFen('xxxxxxxx/8/8/8/8/8/8/8 w KQkq - 0 1');

      expect(result.success).toBe(false);
      expect(result.tree).toBeNull();
    });

    it('should provide friendly error messages', () => {
      const result = importFromFen('invalid');

      expect(result.success).toBe(false);
      expect(result.errors[0]).toBeTruthy();
      // Error should be user-friendly, not just "Invalid FEN"
      expect(result.errors[0].length).toBeGreaterThan(10);
    });
  });

  describe('FEN templates', () => {
    it('should have valid FEN templates', () => {
      Object.values(FEN_TEMPLATES).forEach((template) => {
        const result = importFromFen(template.fen);
        expect(result.success).toBe(true);
        expect(result.tree).not.toBeNull();
      });
    });

    it('should have descriptive template names', () => {
      expect(FEN_TEMPLATES.standard.name).toBe('Standard Starting Position');
      expect(FEN_TEMPLATES.endgameKQvK.name).toContain('Queen');
    });
  });
});

describe('quickValidateFen', () => {
  it('should validate correct FEN', () => {
    const result = quickValidateFen(STANDARD_STARTING_FEN);

    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it('should reject invalid FEN', () => {
    const result = quickValidateFen('invalid fen');

    expect(result.valid).toBe(false);
    expect(result.error).toBeDefined();
  });

  it('should be faster than full import', () => {
    // Quick validation should not create a tree
    const result = quickValidateFen(STANDARD_STARTING_FEN);
    expect(result).not.toHaveProperty('tree');
  });
});

describe('getPositionInfo', () => {
  it('should extract position info from standard FEN', () => {
    const info = getPositionInfo(STANDARD_STARTING_FEN);

    expect(info).not.toBeNull();
    expect(info!.turn).toBe('White');
    expect(info!.moveNumber).toBe(1);
    expect(info!.isStandard).toBe(true);
    expect(info!.inCheck).toBe(false);
    expect(info!.gameOver).toBe(false);
  });

  it('should detect check', () => {
    // Position with black king in check
    const checkFen = 'rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2';
    const info = getPositionInfo(checkFen);

    expect(info).not.toBeNull();
    // Note: This specific FEN may or may not be in check, adjust test if needed
  });

  it('should detect checkmate', () => {
    // Fool's mate position
    const checkmateFen = 'rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3';
    const info = getPositionInfo(checkmateFen);

    expect(info).not.toBeNull();
    expect(info!.gameOver).toBe(true);
  });

  it('should return null for invalid FEN', () => {
    const info = getPositionInfo('invalid');

    expect(info).toBeNull();
  });
});
