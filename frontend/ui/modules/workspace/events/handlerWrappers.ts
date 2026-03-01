// Wrapper functions that connect modules together

import { WorkspaceState, WorkspaceOptions, WorkspaceElements, ModalRoots } from './types';
import { clearCache } from './state';
import { api } from '../../../assets/api';
import { openCreateModal, openMoveModal, openDeleteConfirm, openMoveConfirm, openRenameModal, openNodeActions, openShareModal, openTrashActionsModal } from './modals';
import { refreshNodes as doRefreshNodes, loadMorePublicNodes } from './nodeOperations';
import { navigateToFolder as doNavigateToFolder } from './navigation';
import { renderItems as doRenderItems, appendNodeCards } from './rendering';

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
    let openTrashActionsWrapper: (node: any) => void;

    // ── Infinite scroll state ──────────────────────────────────────────────────
    let _scrollObserver: IntersectionObserver | null = null;
    let _scrollSentinel: HTMLElement | null = null;

    function teardownInfiniteScroll() {
        if (_scrollObserver) { _scrollObserver.disconnect(); _scrollObserver = null; }
        if (_scrollSentinel) { _scrollSentinel.remove(); _scrollSentinel = null; }
    }

    function setupInfiniteScroll() {
        teardownInfiniteScroll();
        const isPublicRoot = state.mode === 'public' && (
            !state.currentParentId || state.currentParentId.startsWith('root')
        );
        if (!isPublicRoot || !state.publicHasMore) return;

        const sentinel = document.createElement('div');
        sentinel.className = 'infinite-scroll-sentinel';
        // Sentinel spans full grid row but is invisible; placed after last card
        sentinel.style.cssText = 'height:1px;grid-column:1/-1;pointer-events:none;';
        elements.itemsGrid.appendChild(sentinel);
        _scrollSentinel = sentinel;

        _scrollObserver = new IntersectionObserver((entries) => {
            if (!entries[0].isIntersecting) return;
            // Disconnect immediately to prevent double-triggering
            if (_scrollObserver) { _scrollObserver.disconnect(); _scrollObserver = null; }
            if (_scrollSentinel) { _scrollSentinel.remove(); _scrollSentinel = null; }

            loadMorePublicNodes(
                state,
                state.currentParentId,
                (newNodes) => appendNodeCards(state, elements, newNodes, {
                    navigateToFolder,
                    openNodeActions: openNodeActionsWrapper,
                }, options),
            ).then((hasMore) => {
                if (hasMore) setupInfiniteScroll();
            });
        }, { threshold: 0.1 });

        _scrollObserver.observe(sentinel);
    }
    // ── End infinite scroll ────────────────────────────────────────────────────

    // refreshNodes implementation
    refreshNodes = async (parentId: string) => {
        teardownInfiniteScroll();
        await doRefreshNodes(state, parentId, renderItems);
    };

    // renderItems implementation
    renderItems = (nodes: any[]) => {
        doRenderItems(state, elements, nodes, options, {
            navigateToFolder,
            openNodeActions: openNodeActionsWrapper,
            openTrashActions: openTrashActionsWrapper,
            openMoveConfirm: openMoveConfirmWrapper,
            openCreateModal: openCreateModalWrapper,
            refreshNodes: () => refreshNodes(state.currentParentId),
        });
        // After rendering, set up infinite scroll if in public root mode
        setupInfiniteScroll();
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

    openTrashActionsWrapper = (node: any) => {
        openTrashActionsModal(
            modalRoots,
            node,
            async (n: any) => {
                await api.post(`/api/v1/workspace/nodes/${n.id}/restore`, {});
                clearCache(state);
                refreshNodes(state.currentParentId);
            },
            async (n: any) => {
                await api.delete(`/api/v1/workspace/nodes/${n.id}/purge?version=${n.version}`);
                clearCache(state);
                refreshNodes(state.currentParentId);
            },
        );
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
