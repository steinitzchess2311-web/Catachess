// Workspace initialization logic

import { api } from '../../../assets/api';
import { WorkspaceState, WorkspaceElements } from './types';
import { renderBreadcrumb, updatePathInputDisplay } from './navigation';

export async function initializeToFolder(
    state: WorkspaceState,
    elements: WorkspaceElements,
    startParentId: string,
    navigateToFolder: (id: string, title: string) => Promise<void>,
    refreshNodes: (parentId: string) => Promise<void>
) {
    if (startParentId && startParentId !== 'root') {
        // Navigate to specific folder
        if (state.mode !== 'private') {
            // Public/shared modes have no auth-free single-node endpoint.
            // Fall back to root; normal navigation will take over from there.
            await navigateToFolder('root', 'root');
            return;
        }
        try {
            console.log(`[WORKSPACE] Initializing to folder: ${startParentId}`);
            const node = await api.get(`/api/v1/workspace/nodes/${startParentId}`);
            if (node) {
                // Build breadcrumb path by traversing parents
                const path: Array<{id: string, title: string}> = [];
                let currentNode = node;
                const visitedNodeIds = new Set<string>();

                while (currentNode) {
                    if (visitedNodeIds.has(currentNode.id)) {
                        console.warn(`[WORKSPACE] Stopped breadcrumb build after detecting a parent cycle at ${currentNode.id}`);
                        break;
                    }
                    visitedNodeIds.add(currentNode.id);
                    path.unshift({ id: currentNode.id, title: currentNode.title });
                    if (!currentNode.parent_id || currentNode.parent_id === 'root') {
                        break;
                    }
                    try {
                        currentNode = await api.get(`/api/v1/workspace/nodes/${currentNode.parent_id}`);
                    } catch {
                        break;
                    }
                }

                // Add root at the beginning
                state.breadcrumbPath = [{ id: 'root', title: 'Root' }, ...path];
                state.currentParentId = startParentId;

                renderBreadcrumb(state, elements, navigateToFolder);
                await refreshNodes(startParentId);
                updatePathInputDisplay(state, elements);

                console.log(`[WORKSPACE] ✓ Initialized to folder: ${node.title}`);
            } else {
                navigateToFolder('root', 'Root');
            }
        } catch (error) {
            console.error(`[WORKSPACE] Failed to load folder ${startParentId}:`, error);
            navigateToFolder('root', 'Root');
        }
    } else {
        navigateToFolder('root', 'Root');
    }
}

export function extractElements(container: HTMLElement) {
    return {
        container,
        itemsGrid: container.querySelector('#items-grid') as HTMLElement,
        breadcrumb: container.querySelector('#breadcrumb') as HTMLElement,
        folderTree: container.querySelector('#folder-tree') as HTMLElement,
        pathInput: container.querySelector('#path-input') as HTMLInputElement | null,
        searchInput: container.querySelector('#workspace-search-input') as HTMLInputElement,
        searchClearBtn: container.querySelector('#workspace-search-clear') as HTMLButtonElement,
        sidebarToggleBtn: container.querySelector('#workspace-sidebar-toggle') as HTMLButtonElement | null,
    };
}
