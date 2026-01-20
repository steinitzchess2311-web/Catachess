/**
 * Tree Schema v1 - Study Tree Data Structure
 *
 * CRITICAL CONSTRAINTS:
 * - Nodes only store SAN, NEVER FEN (FEN is computed via replay)
 * - tree.json must have `version` field at top level
 * - Postgres does not store tree content (stored in R2/file storage)
 * - Custom starting FEN stored in chapter metadata (Postgres), NOT in tree.json
 * - PGN headers reconstructed from study/chapter metadata, NOT stored in tree.json
 *
 * VERSION UPGRADE STRATEGY:
 * When loading a tree, check the `version` field:
 * - If version < TREE_SCHEMA_VERSION: force upgrade migration
 * - If version > TREE_SCHEMA_VERSION: reject (incompatible future version)
 * - If version === TREE_SCHEMA_VERSION: load directly
 *
 * Migration functions should be added to patch/tree/migrations/ as needed.
 */

/** Current schema version - increment when making breaking changes */
export const TREE_SCHEMA_VERSION = 'v1' as const;

/**
 * StudyNode - A single node in the move tree
 *
 * IMPORTANT: No FEN field! FEN is computed on-demand via chess.js replay
 * from the root position through the path of SAN moves.
 *
 * BRANCH ORDER RULE:
 * - children[0] is ALWAYS the mainline continuation
 * - children[1..n] are alternative variations in order of creation
 */
export interface StudyNode {
  /** Unique identifier for this node */
  id: string;

  /** Parent node ID, null only for root node */
  parentId: string | null;

  /**
   * Standard Algebraic Notation for the move
   * Empty string for root node (root has no move)
   */
  san: string;

  /**
   * Child node IDs
   * - children[0] = mainline continuation
   * - children[1..n] = variations (alternatives)
   * Empty array for leaf nodes
   */
  children: string[];

  /**
   * Comment/annotation text for this move
   * null if no comment
   */
  comment: string | null;

  /**
   * Numeric Annotation Glyphs (NAGs)
   * Standard chess annotation symbols encoded as numbers
   * e.g., 1 = !, 2 = ?, 3 = !!, 4 = ??, etc.
   * Empty array if no NAGs
   */
  nags: number[];
}

/**
 * TreeMeta - Metadata stored WITH the tree in tree.json
 *
 * NOTE: This only contains data that belongs to the tree itself.
 * - PGN headers: Reconstructed from study/chapter metadata when exporting (NOT stored here)
 * - Starting FEN: Stored in chapter metadata in Postgres (NOT stored here)
 */
export interface TreeMeta {
  /**
   * Game result: "1-0", "0-1", "1/2-1/2", "*"
   * null if unknown/ongoing
   */
  result: string | null;
}

/**
 * StudyTree - The complete tree structure for a study chapter
 * This is what gets serialized to tree.json
 *
 * ROOT NODE STRUCTURE:
 * - The tree always has a virtual root node
 * - Root node has: san = "", parentId = null, id = rootId
 * - Root's children[0] is the first move of the mainline
 *
 * WHAT IS NOT STORED HERE:
 * - FEN (computed via replay)
 * - Starting FEN (stored in chapter metadata in Postgres)
 * - PGN headers (reconstructed from study/chapter metadata)
 */
export interface StudyTree {
  /** Schema version for migration support */
  version: typeof TREE_SCHEMA_VERSION;

  /** ID of the root node */
  rootId: string;

  /** All nodes indexed by ID */
  nodes: Record<string, StudyNode>;

  /** Tree metadata */
  meta: TreeMeta;
}

/**
 * TreeValidationResult - Result of tree validation
 */
export interface TreeValidationResult {
  valid: boolean;
  errors: string[];
}

export interface TreeUpgradeResult {
  tree: StudyTree | null;
  migrated: boolean;
  errors: string[];
}

/**
 * Validates a StudyTree structure
 *
 * Current checks:
 * - version field exists and matches current version
 * - rootId exists and points to a valid node
 * - root node has no parent and empty san
 * - all child references point to existing nodes
 * - all parent references point to existing nodes
 *
 * @param tree - The tree to validate
 * @returns Validation result with errors if any
 */
export function validateTree(tree: unknown): TreeValidationResult {
  const errors: string[] = [];

  // Type guard
  if (!tree || typeof tree !== 'object') {
    return { valid: false, errors: ['Tree must be an object'] };
  }

  const t = tree as Partial<StudyTree>;

  // Check version
  if (t.version !== TREE_SCHEMA_VERSION) {
    errors.push(`Invalid version: expected "${TREE_SCHEMA_VERSION}", got "${t.version}"`);
  }

  // Check rootId
  if (!t.rootId || typeof t.rootId !== 'string') {
    errors.push('Missing or invalid rootId');
  }

  // Check nodes
  if (!t.nodes || typeof t.nodes !== 'object') {
    errors.push('Missing or invalid nodes');
  } else {
    // Check root node exists
    if (t.rootId && !t.nodes[t.rootId]) {
      errors.push(`Root node "${t.rootId}" not found in nodes`);
    }

    // Check root node structure
    const root = t.rootId ? t.nodes[t.rootId] : undefined;
    if (root) {
      if (root.parentId !== null) {
        errors.push('Root node must have null parentId');
      }
      if (root.san !== '') {
        errors.push('Root node must have empty san');
      }
    }

    // Check all child references are valid
    const nodeIds = new Set(Object.keys(t.nodes));
    for (const [nodeId, node] of Object.entries(t.nodes)) {
      if (!node) continue;

      // Check children references
      for (const childId of node.children || []) {
        if (!nodeIds.has(childId)) {
          errors.push(`Node "${nodeId}" has invalid child reference "${childId}"`);
        }
      }

      // Check parent reference (except root)
      if (node.parentId !== null && !nodeIds.has(node.parentId)) {
        errors.push(`Node "${nodeId}" has invalid parent reference "${node.parentId}"`);
      }
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Upgrade a legacy tree to the current schema version when possible.
 *
 * Supported upgrade:
 * - Missing version -> set to current version (v1)
 */
export function upgradeTree(tree: unknown): TreeUpgradeResult {
  if (!tree || typeof tree !== 'object') {
    return { tree: null, migrated: false, errors: ['Tree must be an object'] };
  }

  const t = tree as Partial<StudyTree>;
  const version = (t as { version?: string }).version;

  if (!version) {
    const upgraded = { ...t, version: TREE_SCHEMA_VERSION } as StudyTree;
    const validation = validateTree(upgraded);
    return {
      tree: validation.valid ? upgraded : null,
      migrated: true,
      errors: validation.errors,
    };
  }

  if (version === TREE_SCHEMA_VERSION) {
    const validation = validateTree(t);
    return {
      tree: validation.valid ? (t as StudyTree) : null,
      migrated: false,
      errors: validation.errors,
    };
  }

  return {
    tree: null,
    migrated: false,
    errors: [`Unsupported version: "${version}"`],
  };
}

/**
 * TreeOperation - Operations that can be applied to a tree
 */
export type TreeOperation =
  | { type: 'ADD_NODE'; parentId: string; node: Omit<StudyNode, 'parentId'> }
  | { type: 'REMOVE_NODE'; nodeId: string }
  | { type: 'UPDATE_COMMENT'; nodeId: string; comment: string | null }
  | { type: 'UPDATE_NAGS'; nodeId: string; nags: number[] }
  | { type: 'PROMOTE_VARIATION'; nodeId: string }
  | { type: 'DELETE_VARIATION'; nodeId: string };

/**
 * TreeCursor - Current position in the tree
 */
export interface TreeCursor {
  /** Current node ID */
  nodeId: string;

  /** Path from root to current node (SAN moves) for replay */
  path: string[];
}
