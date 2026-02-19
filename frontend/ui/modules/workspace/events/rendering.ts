// UI rendering functions
// LEGACY: This workspace module is deprecated. All study functionality has been moved to /patch/

import React from 'react';
import ReactDOM from 'react-dom/client';
import LogoutButton from '../../../../web/src/components/dialogBox/LogoutButton';
import TestSign from '../../../../web/src/components/dialogBox/TestSign';
import { WorkspaceState, WorkspaceElements, WorkspaceOptions } from './types';
import { sortNodes, renameNode } from './nodeOperations';

export function renderItems(
    state: WorkspaceState,
    elements: WorkspaceElements,
    nodes: any[],
    options: WorkspaceOptions,
    handlers: {
        navigateToFolder: (id: string, title: string) => Promise<void>;
        openNodeActions: (node: any, disabledActions?: { move?: boolean; rename?: boolean; delete?: boolean }) => void;
        openMoveConfirm: (source: any, target: any) => void;
        openCreateModal: (type: 'folder' | 'study') => void;
    }
) {
    const sortedNodes = sortNodes(state, nodes);
    state.currentNodes = sortedNodes;
    elements.itemsGrid.innerHTML = '';

    // Insert New Folder / New Study cards as first two grid items (private mode only)
    if (state.mode === 'private') {
        for (const type of ['folder', 'study'] as const) {
            const card = document.createElement('div');
            card.className = 'grid-item new-item-card';
            card.innerHTML = `
                <div class="item-icon" style="font-size:36px;color:var(--text-secondary)">+</div>
                <div class="item-info">
                    <span class="item-title">New ${type === 'folder' ? 'Folder' : 'Study'}</span>
                </div>`;
            card.addEventListener('click', () => handlers.openCreateModal(type));
            elements.itemsGrid.appendChild(card);
        }
    }

    const folderTpl = document.getElementById('folder-item-template') as HTMLTemplateElement;
    const studyTpl = document.getElementById('study-item-template') as HTMLTemplateElement;

    sortedNodes.forEach(node => {
        const tpl = node.node_type === 'folder' ? folderTpl : studyTpl;
        const item = document.importNode(tpl.content, true);
        const itemDiv = item.querySelector('.grid-item') as HTMLElement;
        itemDiv.setAttribute('data-id', node.id);
        itemDiv.setAttribute('data-type', node.node_type);
        itemDiv.setAttribute('data-version', String(node.version));
        itemDiv.setAttribute('data-parent-id', node.parent_id ?? '');
        itemDiv.setAttribute('draggable', state.mode === 'private' ? 'true' : 'false');
        itemDiv.querySelector('.item-title')!.textContent = node.title;
        const errorEl = itemDiv.querySelector('.item-error') as HTMLElement;

        // Display date based on current sort key
        const dateToDisplay = state.sortKey === 'created' ? node.created_at : node.updated_at;
        const date = new Date(dateToDisplay).toLocaleDateString();
        const dateLabel = state.sortKey === 'created' ? 'Created' : 'Modified';
        itemDiv.querySelector('.item-meta')!.textContent = `${dateLabel}: ${date}`;

        itemDiv.addEventListener('click', (event) => {
            if (event.button !== 0) return;
            const target = event.target as HTMLElement;
            if (target.closest('.item-title') || target.closest('.item-title-input')) return;
            if (event.detail > 1) return;
            if (node.node_type === 'folder') {
                handlers.navigateToFolder(node.id, node.title);
                return;
            }
            if (options.onOpenStudy) {
                const topFolder = state.breadcrumbPath[1];
                options.onOpenStudy(node.id, { mode: state.mode, topFolder: topFolder ? topFolder.title : null });
            } else {
                window.location.assign(`/workspace/${node.id}`);
            }
        });

        itemDiv.addEventListener('contextmenu', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const disabledActions = state.mode !== 'private'
                ? { move: true, rename: true, delete: true }
                : undefined;
            handlers.openNodeActions(node, disabledActions);
        });

        const startInlineRename = () => {
            const titleSpan = itemDiv.querySelector('.item-title') as HTMLElement;
            if (!titleSpan) return;
            titleSpan.style.display = 'none';
            const input = document.createElement('input');
            input.className = 'item-title-input';
            input.value = node.title || '';
            titleSpan.parentElement?.insertBefore(input, titleSpan.nextSibling);
            input.focus();
            input.select();
            input.addEventListener('click', (event) => event.stopPropagation());

            let cleanedUp = false;

            const cleanup = () => {
                if (cleanedUp) return;
                cleanedUp = true;
                input.remove();
                titleSpan.style.display = '';
                errorEl.textContent = '';
            };

            input.addEventListener('keydown', async (event) => {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    cleanup();
                    return;
                }
                if (event.key === 'Enter') {
                    event.preventDefault();
                    const nextTitle = input.value.trim();
                    if (!nextTitle) {
                        cleanup();
                        return;
                    }
                    if (nextTitle.includes('/')) {
                        errorEl.textContent = 'No "/" in study or folder name';
                        return;
                    }
                    try {
                        await renameNode(state, node, nextTitle);
                        titleSpan.textContent = node.title;
                        cleanup();
                    } catch (error) {
                        console.error('Failed to rename node:', error);
                        errorEl.textContent = 'Rename failed. Press Enter to retry or Esc to cancel.';
                    }
                }
            });

            input.addEventListener('blur', () => cleanup());
        };

        itemDiv.addEventListener('dblclick', (event) => {
            event.preventDefault();
            event.stopPropagation();
            startInlineRename();
        });

        itemDiv.addEventListener('dragstart', (event) => {
            state.dragNode = node;
            event.dataTransfer?.setData('text/plain', node.id);
            event.dataTransfer?.setDragImage(itemDiv, 10, 10);
        });

        itemDiv.addEventListener('dragend', () => {
            state.dragNode = null;
            itemDiv.classList.remove('drag-over');
        });

        itemDiv.addEventListener('dragover', (event) => {
            if (!state.dragNode) return;
            if (node.node_type !== 'folder') return;
            if (state.dragNode.id === node.id) return;
            event.preventDefault();
            itemDiv.classList.add('drag-over');
        });

        itemDiv.addEventListener('dragleave', () => {
            itemDiv.classList.remove('drag-over');
        });

        itemDiv.addEventListener('drop', async (event) => {
            if (!state.dragNode) return;
            itemDiv.classList.remove('drag-over');
            if (node.node_type !== 'folder' || state.dragNode.id === node.id) {
                itemDiv.classList.remove('drag-over');
                const sourceEl = elements.itemsGrid.querySelector(`[data-id="${state.dragNode.id}"]`) as HTMLElement | null;
                if (sourceEl) {
                    sourceEl.classList.remove('shake');
                    void sourceEl.offsetWidth;
                    sourceEl.classList.add('shake');
                }
                return;
            }
            event.preventDefault();
            handlers.openMoveConfirm(state.dragNode, node);
        });

        elements.itemsGrid.appendChild(item);
    });
}

export function renderReactComponents(
    container: HTMLElement
) {
    // Render LogoutButton
    const logoutContainer = container.querySelector('#logout-button-container') as HTMLElement;
    if (logoutContainer) {
        const root = ReactDOM.createRoot(logoutContainer);
        root.render(React.createElement(LogoutButton));
    }

    // Render TestSign
    const testSignContainer = container.querySelector('#test-sign-container') as HTMLElement;
    if (testSignContainer) {
        const testSignRoot = ReactDOM.createRoot(testSignContainer);
        testSignRoot.render(React.createElement(TestSign));
    }
}
