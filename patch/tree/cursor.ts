/**
 * Cursor utilities for tree navigation
 * Full implementation in Stage 05
 */

import { TreeCursor, StudyNode } from './type';
import { StudyTree } from './StudyTree';

/**
 * Creates a cursor at the root of the tree
 */
export function createCursor(tree: StudyTree): TreeCursor {
  return tree.createCursor();
}

/**
 * Creates a cursor at a specific node
 */
export function createCursorAt(tree: StudyTree, nodeId: string): TreeCursor {
  return tree.createCursor(nodeId);
}

/**
 * Moves cursor to a specific node (alias for createCursorAt)
 * Returns the new cursor with updated path.
 */
export function moveTo(tree: StudyTree, nodeId: string): TreeCursor {
  return tree.createCursor(nodeId);
}

/**
 * Returns the list of SAN moves from root to the target node.
 * Legacy name; prefer pathToRootSan/getPathSan for clarity.
 */
export function pathToRoot(tree: StudyTree, nodeId: string): string[] {
  return tree.getPathSan(nodeId);
}

/**
 * Returns the list of SAN moves from root to the target node.
 * Preferred name for clarity.
 */
export function pathToRootSan(tree: StudyTree, nodeId: string): string[] {
  return tree.getPathSan(nodeId);
}

/**
 * Returns the list of SAN moves from root to the target node.
 * Used for replay. (Alias for pathToRoot now)
 */
export function getPathSan(tree: StudyTree, nodeId: string): string[] {
  return tree.getPathSan(nodeId);
}

/**
 * Gets the current node ID from a cursor
 */
export function getCursorNodeId(cursor: TreeCursor): string {
  return cursor.nodeId;
}

/**
 * Gets the current node from a cursor
 */
export function getCursorNode(cursor: TreeCursor, tree: StudyTree): StudyNode | undefined {
  return tree.getNode(cursor.nodeId);
}

/**
 * Moves cursor to parent node
 */
export function moveCursorToParent(cursor: TreeCursor, tree: StudyTree): TreeCursor {
  const node = tree.getNode(cursor.nodeId);
  if (!node || node.parentId === null) {
    return cursor; // Already at root or node not found
  }

  return tree.createCursor(node.parentId);
}

/**
 * Moves cursor to mainline child (children[0])
 */
export function moveCursorToMainline(cursor: TreeCursor, tree: StudyTree): TreeCursor {
  const node = tree.getNode(cursor.nodeId);
  if (!node || node.children.length === 0) {
    return cursor; // No children
  }

  return tree.createCursor(node.children[0]);
}

/**
 * Moves cursor to a specific variation
 * @param variationIndex - Index in children array (0 = mainline)
 */
export function moveCursorToVariation(
  cursor: TreeCursor,
  tree: StudyTree,
  variationIndex: number
): TreeCursor {
  const node = tree.getNode(cursor.nodeId);
  if (!node || variationIndex >= node.children.length) {
    return cursor; // Invalid index
  }

  return tree.createCursor(node.children[variationIndex]);
}

/**
 * Gets the path from the cursor (list of SAN moves from root)
 */
export function getCursorPath(cursor: TreeCursor): string[] {
  return [...cursor.path];
}

/**
 * Checks if cursor is at root
 */
export function isAtRoot(cursor: TreeCursor, tree: StudyTree): boolean {
  return cursor.nodeId === tree.getRootId();
}

/**
 * Checks if cursor is at a leaf node (no children)
 */
export function isAtLeaf(cursor: TreeCursor, tree: StudyTree): boolean {
  const node = tree.getNode(cursor.nodeId);
  return !node || node.children.length === 0;
}
