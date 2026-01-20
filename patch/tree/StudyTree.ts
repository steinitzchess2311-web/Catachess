/**
 * StudyTree class - Tree operations
 * Full implementation pending Stage 05
 */

import {
  StudyTree as StudyTreeData,
  StudyNode,
  TreeMeta,
  TreeCursor,
  TreeValidationResult,
  validateTree,
  TREE_SCHEMA_VERSION,
} from './type';

/**
 * Creates an empty tree with just a root node
 *
 * NOTE: This creates only the tree.json content.
 * - Starting FEN is stored in chapter metadata (Postgres), not here
 * - PGN headers are reconstructed from study/chapter metadata when exporting
 */
export function createEmptyTree(): StudyTreeData {
  const rootId = 'root';
  return {
    version: TREE_SCHEMA_VERSION,
    rootId,
    nodes: {
      [rootId]: {
        id: rootId,
        parentId: null,
        san: '',
        children: [],
        comment: null,
        nags: [],
      },
    },
    meta: {
      result: null,
    },
  };
}

/**
 * StudyTree class for tree manipulation
 * Full implementation in Stage 05
 */
export class StudyTree {
  private data: StudyTreeData;

  constructor(initialData?: StudyTreeData) {
    this.data = initialData || createEmptyTree();
  }

  getRootId(): string {
    return this.data.rootId;
  }

  getNode(nodeId: string): StudyNode | undefined {
    return this.data.nodes[nodeId];
  }

  getRoot(): StudyNode {
    return this.data.nodes[this.data.rootId];
  }

  getAllNodes(): Record<string, StudyNode> {
    return { ...this.data.nodes };
  }

  getData(): StudyTreeData {
    return { ...this.data };
  }

  getMeta(): TreeMeta {
    return { ...this.data.meta };
  }

  getVersion(): string {
    return this.data.version;
  }

  /**
   * Validates the tree structure
   */
  validate(): TreeValidationResult {
    return validateTree(this.data);
  }

  /**
   * Gets the mainline (children[0] path from root)
   */
  getMainline(): StudyNode[] {
    const result: StudyNode[] = [];
    let current = this.getRoot();

    while (current.children.length > 0) {
      const nextId = current.children[0]; // mainline is always children[0]
      const next = this.data.nodes[nextId];
      if (!next) break;
      result.push(next);
      current = next;
    }

    return result;
  }

  /**
   * Gets the path from root to a specific node
   */
  getPathToNode(nodeId: string): string[] {
    const path: string[] = [];
    let current = this.data.nodes[nodeId];

    while (current) {
      path.unshift(current.id);
      if (current.parentId === null) break;
      current = this.data.nodes[current.parentId];
    }

    return path;
  }

  /**
   * Gets the path of SAN moves from root to a specific node.
   * Root node (empty SAN) is excluded.
   * Useful for replay.
   */
  getPathSan(nodeId: string): string[] {
    const pathIds = this.getPathToNode(nodeId);
    const sanPath: string[] = [];
    
    // Skip root (index 0)
    for (let i = 1; i < pathIds.length; i++) {
      const node = this.data.nodes[pathIds[i]];
      if (node) {
        sanPath.push(node.san);
      }
    }
    
    return sanPath;
  }

  /**
   * Creates a cursor at the given node
   * Returns SAN moves in the path for replay.
   */
  createCursor(nodeId?: string): TreeCursor {
    const targetId = nodeId || this.data.rootId;
    return {
      nodeId: targetId,
      path: this.getPathSan(targetId),
    };
  }

  /**
   * Adds a move to the tree under the specified parent
   * If a child with the same SAN already exists, returns it instead of creating a new one
   */
  addMove(parentId: string, san: string): StudyNode {
    const parent = this.data.nodes[parentId];
    if (!parent) {
      throw new Error(`Parent node ${parentId} not found`);
    }

    // Check for existing move (transposition/duplicate)
    for (const childId of parent.children) {
      const child = this.data.nodes[childId];
      if (child && child.san === san) {
        return child;
      }
    }

    // Create new node
    const newNodeId = this.generateId();
    const newNode: StudyNode = {
      id: newNodeId,
      parentId: parentId,
      san,
      children: [],
      comment: null,
      nags: [],
    };

    // Update state
    this.data.nodes[newNodeId] = newNode;
    parent.children.push(newNodeId);

    return newNode;
  }

  /**
   * Deletes a node and its subtree
   * Constraint: Cannot delete root node.
   * Constraint: Must handle orphan nodes (recursive delete).
   */
  removeNode(nodeId: string): void {
    const node = this.data.nodes[nodeId];
    if (!node) return;

    if (node.id === this.data.rootId) {
      throw new Error('Cannot delete root node');
    }

    // Remove from parent
    if (node.parentId) {
      const parent = this.data.nodes[node.parentId];
      if (parent) {
        parent.children = parent.children.filter((id) => id !== nodeId);
      }
    }

    // Recursively delete children (prevent orphans)
    this.deleteSubtree(nodeId);
  }

  /**
   * Promotes a variation to the mainline (children[0])
   * Constraint: Mainline is always children[0].
   */
  promoteVariation(nodeId: string): void {
    const node = this.data.nodes[nodeId];
    if (!node || !node.parentId) return; // Cannot promote root or orphan

    const parent = this.data.nodes[node.parentId];
    if (!parent) return;

    const index = parent.children.indexOf(nodeId);
    if (index <= 0) return; // Already mainline or not found

    // Swap with the previous sibling (bubbling up)
    // Or move directly to 0? "Promote to mainline" usually means "make it the main line".
    // If I just swap with 0, the old mainline becomes a variation.
    // Let's move it to index 0 and shift others down.
    
    // Remove from current position
    parent.children.splice(index, 1);
    // Insert at start
    parent.children.unshift(nodeId);
  }

  /**
   * Demotes a variation (or mainline) down the list
   * Constraint: Mainline is always children[0].
   */
  demoteVariation(nodeId: string): void {
    const node = this.data.nodes[nodeId];
    if (!node || !node.parentId) return;

    const parent = this.data.nodes[node.parentId];
    if (!parent) return;

    const index = parent.children.indexOf(nodeId);
    if (index === -1 || index === parent.children.length - 1) return; // Already last or not found

    // Swap with next sibling
    const nextId = parent.children[index + 1];
    parent.children[index] = nextId;
    parent.children[index + 1] = nodeId;
  }

  private deleteSubtree(nodeId: string) {
    const node = this.data.nodes[nodeId];
    if (!node) return;

    for (const childId of node.children) {
      this.deleteSubtree(childId);
    }

    delete this.data.nodes[nodeId];
  }

  private generateId(): string {
    return Math.random().toString(36).substring(2, 10) + Date.now().toString(36).substring(4);
  }
}

export default StudyTree;
