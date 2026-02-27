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

export async function refreshNodes(state: WorkspaceState, parentId: string, renderItems: (nodes: any[]) => void) {
    let url: string;
    if (state.mode === 'public') {
        url = `/api/v1/workspace/public-nodes?parent_id=${parentId}`;
    } else if (state.mode === 'shared') {
        url = `/api/v1/workspace/shared-nodes?parent_id=${parentId}`;
    } else if (state.mode === 'trash') {
        url = `/api/v1/workspace/nodes/trash`;
    } else {
        url = `/api/v1/workspace/nodes?parent_id=${parentId}`;
    }
    try {
        const response = await api.get(url);
        renderItems(response.nodes);
    } catch (error) {
        console.error('Failed to fetch nodes:', error);
        renderItems([]);
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
