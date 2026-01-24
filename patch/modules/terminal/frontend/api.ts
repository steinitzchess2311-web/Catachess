/**
 * Terminal API Client
 * Interfaces with the real backend workspace API
 */

import { api } from '@ui/assets/api';

// =============================================================================
// Types
// =============================================================================

export interface WorkspaceNode {
  id: string;
  node_type: 'workspace' | 'folder' | 'study';
  title: string;
  description?: string;
  parent_id?: string;
  visibility: 'private' | 'public';
  path?: string;
  depth?: number;
  created_at?: string;
  updated_at?: string;
  deleted_at?: string;
  version?: number;
}

export interface CreateNodeRequest {
  node_type: 'folder' | 'study';
  title: string;
  description?: string;
  parent_id?: string;
  visibility?: 'private' | 'public';
}

export interface DeleteNodeRequest {
  version?: number;
}

// =============================================================================
// API Functions
// =============================================================================

const BASE_URL = '/api/v1/workspace';

/**
 * Get root nodes (workspaces)
 */
export async function getRootNodes(): Promise<WorkspaceNode[]> {
  try {
    const response = await api.get(`${BASE_URL}/nodes`);
    // API returns { nodes: [...], total: number }
    return response?.nodes || [];
  } catch (e) {
    console.error('[terminal-api] Failed to get root nodes:', e);
    return [];
  }
}

/**
 * Get children of a node
 */
export async function getNodeChildren(nodeId: string): Promise<WorkspaceNode[]> {
  try {
    const response = await api.get(`${BASE_URL}/nodes/${nodeId}/children`);
    // API returns { nodes: [...], total: number }
    return response?.nodes || [];
  } catch (e) {
    console.error('[terminal-api] Failed to get children:', e);
    return [];
  }
}

/**
 * Get a single node by ID
 */
export async function getNode(nodeId: string): Promise<WorkspaceNode | null> {
  try {
    const response = await api.get(`${BASE_URL}/nodes/${nodeId}`);
    return response;
  } catch (e) {
    console.error('[terminal-api] Failed to get node:', e);
    return null;
  }
}

/**
 * Create a new folder
 */
export async function createFolder(
  title: string,
  parentId?: string
): Promise<WorkspaceNode | null> {
  try {
    const response = await api.post(`${BASE_URL}/nodes`, {
      node_type: 'folder',
      title,
      parent_id: parentId,
      visibility: 'private',
    });
    return response;
  } catch (e) {
    console.error('[terminal-api] Failed to create folder:', e);
    throw e;
  }
}

/**
 * Create a new study
 */
export async function createStudy(
  title: string,
  parentId?: string
): Promise<WorkspaceNode | null> {
  try {
    const response = await api.post(`${BASE_URL}/studies`, {
      title,
      parent_id: parentId,
      visibility: 'private',
    });
    return response;
  } catch (e) {
    console.error('[terminal-api] Failed to create study:', e);
    throw e;
  }
}

/**
 * Delete a node (soft delete)
 */
export async function deleteNode(
  nodeId: string,
  version?: number
): Promise<boolean> {
  try {
    await api.delete(`${BASE_URL}/nodes/${nodeId}`, {
      version: version || 1,
    });
    return true;
  } catch (e) {
    console.error('[terminal-api] Failed to delete node:', e);
    throw e;
  }
}

/**
 * Move a node to a new parent
 */
export async function moveNode(
  nodeId: string,
  newParentId: string,
  version?: number
): Promise<boolean> {
  try {
    await api.post(`${BASE_URL}/nodes/${nodeId}/move`, {
      new_parent_id: newParentId,
      version: version || 1,
    });
    return true;
  } catch (e) {
    console.error('[terminal-api] Failed to move node:', e);
    throw e;
  }
}

// =============================================================================
// Path Resolution Cache
// =============================================================================

interface PathCacheEntry {
  nodeId: string;
  node: WorkspaceNode;
  children?: WorkspaceNode[];
  timestamp: number;
}

const pathCache = new Map<string, PathCacheEntry>();
const CACHE_TTL = 30000; // 30 seconds

/**
 * Resolve a path to a node ID
 * Caches results for performance
 */
export async function resolvePathToNode(
  path: string,
  rootNodeId?: string
): Promise<WorkspaceNode | null> {
  // Normalize path
  const normalizedPath = path.replace(/\/+/g, '/').replace(/\/$/, '') || '/';

  // Check cache
  const cached = pathCache.get(normalizedPath);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.node;
  }

  // Handle root
  if (normalizedPath === '/' || normalizedPath === '') {
    const roots = await getRootNodes();
    if (roots.length > 0) {
      const root = roots[0];
      pathCache.set('/', {
        nodeId: root.id,
        node: root,
        timestamp: Date.now(),
      });
      return root;
    }
    return null;
  }

  // Split path and traverse
  const parts = normalizedPath.split('/').filter(Boolean);
  let currentNode: WorkspaceNode | null = null;

  // Start from root
  const roots = await getRootNodes();
  if (roots.length === 0) return null;

  // Check if first part matches a root workspace
  const rootMatch = roots.find(r => r.title === parts[0]);
  if (rootMatch) {
    currentNode = rootMatch;
    parts.shift();
  } else {
    currentNode = roots[0];
  }

  // Traverse path
  for (const part of parts) {
    if (!currentNode) return null;

    const children = await getNodeChildren(currentNode.id);
    const child = children.find(c => c.title === part);

    if (!child) return null;
    currentNode = child;
  }

  // Cache result
  if (currentNode) {
    pathCache.set(normalizedPath, {
      nodeId: currentNode.id,
      node: currentNode,
      timestamp: Date.now(),
    });
  }

  return currentNode;
}

/**
 * Get the display path for a node
 */
export async function getNodePath(nodeId: string): Promise<string> {
  const parts: string[] = [];
  let currentId: string | undefined = nodeId;

  while (currentId) {
    const node = await getNode(currentId);
    if (!node) break;
    parts.unshift(node.title);
    currentId = node.parent_id;
  }

  return '/' + parts.join('/');
}

/**
 * Clear path cache
 */
export function clearPathCache(): void {
  pathCache.clear();
}

/**
 * Invalidate cache for a specific path and its children
 */
export function invalidatePathCache(path: string): void {
  for (const key of pathCache.keys()) {
    if (key.startsWith(path)) {
      pathCache.delete(key);
    }
  }
}
