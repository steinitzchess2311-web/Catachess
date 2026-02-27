// State management for workspace

import { WorkspaceState, SortKey, SortDir, WorkspaceMode } from './types';

export function createInitialState(startParentId: string): WorkspaceState {
    return {
        currentParentId: startParentId,
        breadcrumbPath: [{id: 'root', title: 'Root'}],
        allNodesCache: null,
        dragNode: null,
        sortKey: 'modified' as SortKey,
        sortDir: 'desc' as SortDir,
        isBatchMode: false,
        selectedItemIds: new Set<string>(),
        currentNodes: [],
        mode: 'private' as WorkspaceMode,
    };
}

export function setMode(state: WorkspaceState, mode: WorkspaceMode) {
    state.mode = mode;
    const rootLabel = { private: 'Root', public: 'Public', shared: 'Shared', trash: 'Trash' }[mode];
    state.breadcrumbPath = [{ id: 'root', title: rootLabel }];
}

export function clearCache(state: WorkspaceState) {
    state.allNodesCache = null;
}

export function setDragNode(state: WorkspaceState, node: any | null) {
    state.dragNode = node;
}

export function setSortSettings(state: WorkspaceState, sortKey: SortKey, sortDir: SortDir) {
    state.sortKey = sortKey;
    state.sortDir = sortDir;
}

export function toggleBatchMode(state: WorkspaceState) {
    state.isBatchMode = !state.isBatchMode;
    if (!state.isBatchMode) {
        state.selectedItemIds.clear();
    }
}

export function exitBatchMode(state: WorkspaceState) {
    state.isBatchMode = false;
    state.selectedItemIds.clear();
}

export function toggleItemSelection(state: WorkspaceState, itemId: string) {
    if (state.selectedItemIds.has(itemId)) {
        state.selectedItemIds.delete(itemId);
    } else {
        state.selectedItemIds.add(itemId);
    }
}
