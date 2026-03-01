// Node CRUD operations

import { api } from '../../../assets/api';
import { WorkspaceState } from './types';

export function sortNodes(state: WorkspaceState, nodes: any[]): any[] {
    if (!state.sortKey) return nodes;

    const sorted = [...nodes].sort((a, b) => {
        let aValue: string;
        let bValue: string;

        if (state.sortKey === 'created') {
            aValue = a.created_at;
            bValue = b.created_at;
        } else {
            aValue = a.updated_at;
            bValue = b.updated_at;
        }

        const comparison = aValue.localeCompare(bValue);
        return state.sortDir === 'asc' ? comparison : -comparison;
    });

    return sorted;
}

const PUBLIC_PAGE_SIZE = 40;

export async function refreshNodes(state: WorkspaceState, parentId: string, renderItems: (nodes: any[]) => void) {
    let url: string;
    const isPublicRoot = state.mode === 'public' && (!parentId || parentId.startsWith('root'));

    if (state.mode === 'public') {
        if (isPublicRoot) {
            // Reset pagination on every fresh navigation
            state.publicOffset = 0;
            url = `/api/v1/workspace/public-nodes?parent_id=${parentId}&limit=${PUBLIC_PAGE_SIZE}&offset=0`;
        } else {
            url = `/api/v1/workspace/public-nodes?parent_id=${parentId}`;
        }
    } else if (state.mode === 'shared') {
        url = `/api/v1/workspace/shared-nodes?parent_id=${parentId}`;
    } else if (state.mode === 'trash') {
        url = `/api/v1/workspace/nodes/trash`;
    } else {
        url = `/api/v1/workspace/nodes?parent_id=${parentId}`;
    }
    try {
        const response = await api.get(url);
        if (isPublicRoot) {
            state.publicHasMore = response.nodes.length === PUBLIC_PAGE_SIZE;
        }
        renderItems(response.nodes);
    } catch (error) {
        console.error('Failed to fetch nodes:', error);
        renderItems([]);
    }
}

/**
 * Fetch the next page of public root nodes and append their cards to the grid
 * without clearing existing cards. Used by IntersectionObserver infinite scroll.
 *
 * Returns true if there may be more pages, false when exhausted.
 */
export async function loadMorePublicNodes(
    state: WorkspaceState,
    parentId: string,
    appendCards: (newNodes: any[]) => void,
): Promise<boolean> {
    state.publicOffset += PUBLIC_PAGE_SIZE;
    const url = `/api/v1/workspace/public-nodes?parent_id=${parentId}&limit=${PUBLIC_PAGE_SIZE}&offset=${state.publicOffset}`;
    try {
        const response = await api.get(url);
        const newNodes: any[] = response.nodes ?? [];
        state.publicHasMore = newNodes.length === PUBLIC_PAGE_SIZE;
        if (newNodes.length > 0) {
            // Add to currentNodes so state stays consistent
            state.currentNodes = [...state.currentNodes, ...newNodes];
            appendCards(newNodes);
        }
        return state.publicHasMore;
    } catch (error) {
        console.error('Failed to load more public nodes:', error);
        state.publicHasMore = false;
        return false;
    }
}

export async function renameNode(state: WorkspaceState, node: any, title: string) {
    const trimmed = title.trim();
    if (!trimmed) return false;
    if (trimmed.includes('/')) return false;

    try {
        const response = await api.put(`/api/v1/workspace/nodes/${node.id}`, {
            title: trimmed,
            version: node.version,
        });
        node.title = response.title;
        node.version = response.version;
        state.allNodesCache = null;
        return true;
    } catch (error: any) {
        // Handle version conflict (409) by fetching latest version and retrying
        if (error.message && error.message.includes('Version conflict')) {
            try {
                console.log(`[WORKSPACE] Version conflict detected, fetching latest version for node ${node.id}`);
                const latestNode = await api.get(`/api/v1/workspace/nodes/${node.id}`);
                const retryResponse = await api.put(`/api/v1/workspace/nodes/${node.id}`, {
                    title: trimmed,
                    version: latestNode.version,
                });
                node.title = retryResponse.title;
                node.version = retryResponse.version;
                state.allNodesCache = null;
                console.log(`[WORKSPACE] ✓ Rename succeeded after version refresh`);
                return true;
            } catch (retryError) {
                console.error('Failed to rename node after retry:', retryError);
                throw retryError;
            }
        }
        throw error;
    }
}
