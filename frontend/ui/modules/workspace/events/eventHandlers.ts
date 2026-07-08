// Event handlers setup

import { WorkspaceState, WorkspaceElements, WorkspaceOptions, WorkspaceMode } from './types';
import { getPathPrefix, getRootPrefix, getRootLabel, shakePathInput, resolvePath } from './navigation';
import { setMode, clearCache } from './state';
import { runSearch } from './search';

const SIDEBAR_COLLAPSED_KEY = 'cata.workspace.sidebarCollapsed';

export function applySidebarCollapsedState(
    elements: WorkspaceElements,
    collapsed: boolean,
    persist = true
) {
    const shell = elements.container.querySelector<HTMLElement>('.workspace-container') ?? elements.container;
    shell.classList.toggle('workspace-container--sidebar-collapsed', collapsed);
    if (elements.sidebarToggleBtn) {
        elements.sidebarToggleBtn.setAttribute('aria-expanded', String(!collapsed));
        elements.sidebarToggleBtn.setAttribute(
            'aria-label',
            collapsed ? 'Expand sidebar' : 'Collapse sidebar'
        );
        elements.sidebarToggleBtn.title = collapsed ? 'Expand sidebar' : 'Collapse sidebar';
    }
    if (!persist) return;
    try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed ? '1' : '0');
    } catch {
        // Ignore storage failures; the UI state still applies for this session.
    }
}

export function getStoredSidebarCollapsed() {
    try {
        return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1';
    } catch {
        return false;
    }
}

export function setupEventHandlers(
    state: WorkspaceState,
    elements: WorkspaceElements,
    options: WorkspaceOptions,
    handlers: {
        openCreateModal: (type: 'folder' | 'study') => void;
        navigateToFolder: (id: string, title: string) => Promise<void>;
        renderItems: (nodes: any[]) => void;
        refreshNodes: (parentId: string) => Promise<void>;
    }
) {
    elements.sidebarToggleBtn?.addEventListener('click', () => {
        const shell = elements.container.querySelector<HTMLElement>('.workspace-container') ?? elements.container;
        const collapsed = !shell.classList.contains('workspace-container--sidebar-collapsed');
        applySidebarCollapsedState(elements, collapsed);
    });

    // Mode nav buttons
    elements.container.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = (btn as HTMLElement).dataset.mode as WorkspaceMode;
            elements.container.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setMode(state, mode);
            if (elements.pathInput) {
                elements.pathInput.placeholder = `${getRootPrefix(state)}...`;
            }
            const createActions = elements.container.querySelector<HTMLElement>('.workspace-create-actions');
            if (createActions) {
                createActions.hidden = mode !== 'private';
            }
            clearCache(state);
            handlers.navigateToFolder('root', getRootLabel(state));
        });
    });

    elements.container.querySelectorAll<HTMLElement>('[data-create-type]').forEach((button) => {
        button.addEventListener('click', () => {
            if (state.mode !== 'private') return;
            const type = button.dataset.createType;
            if (type === 'folder' || type === 'study') {
                handlers.openCreateModal(type);
            }
        });
    });

    // Path input - Enter key
    elements.pathInput?.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        resolvePath(
            state,
            elements,
            elements.pathInput.value,
            options,
            handlers.navigateToFolder
        ).catch(() => shakePathInput(elements));
    });

    // Path input - Focus
    elements.pathInput?.addEventListener('focus', () => {
        const prefix = getPathPrefix(state);
        if (elements.pathInput.value.endsWith('/...')) {
            elements.pathInput.value = prefix;
        }
    });

    // Path input - Blur
    elements.pathInput?.addEventListener('blur', () => {
        const prefix = getPathPrefix(state);
        if (elements.pathInput.value === prefix) {
            elements.pathInput.value = `${prefix}...`;
        }
    });

    // Path input - Prevent deleting mode prefix
    elements.pathInput?.addEventListener('keydown', (event) => {
        if (event.key !== 'Backspace') return;
        const start = elements.pathInput.selectionStart ?? 0;
        const rootPrefix = getRootPrefix(state);
        if (start <= rootPrefix.length) {
            event.preventDefault();
        }
    });

    // Path input - Auto-prepend mode prefix
    elements.pathInput?.addEventListener('input', () => {
        const rootPrefix = getRootPrefix(state);
        if (!elements.pathInput.value.startsWith(rootPrefix)) {
            elements.pathInput.value = `${rootPrefix}${elements.pathInput.value.replace(/^\/+/, '')}`;
        }
    });

    // Search input - Enter key
    elements.searchInput?.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;
        event.preventDefault();
        console.log('[Search] Running search for:', elements.searchInput.value);
        runSearch(state, elements.searchInput.value, handlers.renderItems, handlers.refreshNodes).catch((err) => {
            console.error('[Search] Search failed:', err);
        });
    });

    // Search clear button
    elements.searchClearBtn?.addEventListener('click', () => {
        elements.searchInput.value = '';
        window.location.reload();
    });

    // Items grid - dragover
    elements.itemsGrid.addEventListener('dragover', (event) => {
        if (!state.dragNode) return;
        event.preventDefault();
    });
}
