// Wrapper functions that connect modules together

import { WorkspaceState, WorkspaceOptions, WorkspaceElements, ModalRoots } from './types';
import { clearCache } from './state';
import { openCreateModal, openMoveModal, openDeleteConfirm, openMoveConfirm, openRenameModal, openNodeActions, openShareModal } from './modals';
import { refreshNodes as doRefreshNodes } from './nodeOperations';
import { navigateToFolder as doNavigateToFolder } from './navigation';
import { renderItems as doRenderItems } from './rendering';

export function createHandlerWrappers(
    state: WorkspaceState,
    elements: WorkspaceElements,
    options: WorkspaceOptions,
    modalRoots: ModalRoots
) {
    // Forward declarations for mutual dependencies
    let refreshNodes: (parentId: string) => Promise<void>;
    let renderItems: (nodes: any[]) => void;
    let navigateToFolder: (id: string, title: string) => Promise<void>;
    let openNodeActionsWrapper: (node: any, disabledActions?: { move?: boolean; rename?: boolean; delete?: boolean }) => void;

    // refreshNodes implementation
    refreshNodes = async (parentId: string) => {
        await doRefreshNodes(state, parentId, renderItems);
    };

    // renderItems implementation
    renderItems = (nodes: any[]) => {
        doRenderItems(state, elements, nodes, options, {
            navigateToFolder,
            openNodeActions: openNodeActionsWrapper,
            openMoveConfirm: openMoveConfirmWrapper,
            openCreateModal: openCreateModalWrapper,
            refreshNodes: () => refreshNodes(state.currentParentId),
        });
    };

    // navigateToFolder implementation
    navigateToFolder = async (id: string, title: string) => {
        await doNavigateToFolder(state, elements, id, title, refreshNodes);
        if (options.onWorkspaceNavigate) {
            const topFolder = state.breadcrumbPath[1];
            options.onWorkspaceNavigate(state.mode, topFolder ? topFolder.title : null);
        }
    };

    // Modal wrappers
    const openCreateModalWrapper = (type: 'folder' | 'study') => {
        openCreateModal(modalRoots, type, state.currentParentId, () => {
            clearCache(state);
            refreshNodes(state.currentParentId);
        });
    };

    const openMoveModalWrapper = (node: any) => {
        openMoveModal(modalRoots, node, () => {
            clearCache(state);
            refreshNodes(state.currentParentId);
        });
    };

    const openDeleteConfirmWrapper = (node: any) => {
        openDeleteConfirm(modalRoots, node, () => {
            clearCache(state);
            refreshNodes(state.currentParentId);
        });
    };

    const openMoveConfirmWrapper = (source: any, target: any) => {
        openMoveConfirm(modalRoots, source, target, () => {
            clearCache(state);
            refreshNodes(state.currentParentId);
        });
    };

    const openRenameModalWrapper = (node: any) => {
        openRenameModal(modalRoots, node, () => {
            clearCache(state);
            refreshNodes(state.currentParentId);
        });
    };

    const openShareModalWrapper = (node: any) => {
        openShareModal(modalRoots, node);
    };

    openNodeActionsWrapper = (node: any, disabledActions?: { move?: boolean; rename?: boolean; delete?: boolean }) => {
        openNodeActions(
            modalRoots,
            node,
            openMoveModalWrapper,
            openRenameModalWrapper,
            openDeleteConfirmWrapper,
            openShareModalWrapper,
            disabledActions
        );
    };

    return {
        refreshNodes,
        renderItems,
        navigateToFolder,
        openCreateModalWrapper,
        openMoveModalWrapper,
        openDeleteConfirmWrapper,
        openMoveConfirmWrapper,
        openRenameModalWrapper,
        openNodeActionsWrapper,
        openShareModalWrapper,
    };
}
