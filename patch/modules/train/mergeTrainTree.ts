/**
 * mergeTrainTree.ts - Merge draft tree into main study tree on submit.
 *
 * Algorithm:
 * - Clone mainTree via structuredClone
 * - Recursively walk draft from draftRootId, anchoring into main at mainAnchorNodeId
 * - Match found (same SAN): mark existing node trained: true, recurse into children
 * - No match: create new StudyNode with trained: true, push to mainNode.children
 * - Comments: draft + main → append; draft only → use as-is
 */

import type { StudyTree as StudyTreeData, StudyNode } from '../../tree/type';
import type { DraftNode } from './useDraftTree';

function generateId(): string {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36).substring(4);
}

function mergeNode(
  mainNodes: Record<string, StudyNode>,
  mainAnchorId: string,
  draftNodes: Record<string, DraftNode>,
  draftNodeId: string
): void {
  const draftNode = draftNodes[draftNodeId];
  if (!draftNode) return;

  const mainAnchor = mainNodes[mainAnchorId];
  if (!mainAnchor) return;

  // Find matching child in main by SAN
  const matchingChildId = mainAnchor.children.find(
    (cId) => mainNodes[cId]?.san === draftNode.san
  );

  let targetMainId: string;

  if (matchingChildId) {
    // Match found: mark trained, merge comment
    const existing = mainNodes[matchingChildId];
    const mergedComment = mergeComment(existing.comment, draftNode.comment);
    mainNodes[matchingChildId] = { ...existing, trained: true, comment: mergedComment };
    targetMainId = matchingChildId;
  } else {
    // No match: create new node
    const newId = generateId();
    const newNode: StudyNode = {
      id: newId,
      parentId: mainAnchorId,
      san: draftNode.san,
      children: [],
      comment: draftNode.comment || null,
      nags: [],
      trained: true,
    };
    mainNodes[newId] = newNode;
    mainAnchor.children.push(newId);
    targetMainId = newId;
  }

  // Recurse into draft children
  for (const childDraftId of draftNode.children) {
    mergeNode(mainNodes, targetMainId, draftNodes, childDraftId);
  }
}

function mergeComment(mainComment: string | null, draftComment: string): string | null {
  const trimmedDraft = draftComment.trim();
  if (!trimmedDraft) return mainComment;
  if (!mainComment) return trimmedDraft;
  return `${mainComment}\n[train mode]: ${trimmedDraft}`;
}

export function mergeTrainTree(
  mainTree: StudyTreeData,
  draftNodes: Record<string, DraftNode>,
  draftRootId: string,
  mainAnchorNodeId: string
): StudyTreeData {
  const cloned = structuredClone(mainTree) as StudyTreeData;

  const draftRoot = draftNodes[draftRootId];
  if (!draftRoot) return cloned;

  // Merge each direct child of draft root into the main anchor node
  for (const childDraftId of draftRoot.children) {
    mergeNode(cloned.nodes, mainAnchorNodeId, draftNodes, childDraftId);
  }

  return cloned;
}
