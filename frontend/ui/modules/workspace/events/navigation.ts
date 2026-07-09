// Navigation and path management

import { api } from '../../../assets/api';
import { WorkspaceState, WorkspaceElements, WorkspaceMode } from './types';

const MAX_VISIBLE_BREADCRUMB_ITEMS = 4;
const TRAILING_BREADCRUMB_ITEMS = 2;
const MAX_BREADCRUMB_LABEL_CHARS = 28;

type BreadcrumbEntry = { id: string; title: string };

export function getRootPrefix(state: WorkspaceState): string {
    const map: Record<string, string> = { private: 'root/', public: 'public/', shared: 'shared/', trash: 'trash/' };
    return map[state.mode ?? 'private'] ?? 'root/';
}

export function getRootLabel(state: WorkspaceState): string {
    const map: Record<string, string> = { private: 'Root', public: 'Public', shared: 'Shared', trash: 'Trash' };
    return map[state.mode ?? 'private'] ?? 'Root';
}

export function getPathPrefix(state: WorkspaceState) {
    const base = getRootPrefix(state).slice(0, -1); // strip trailing slash
    const segments = state.breadcrumbPath
        .map((item) => item.title)
        .filter((_, idx) => idx > 0);
    if (segments.length === 0) return `${base}/`;
    return `${base}/${segments.join('/')}/`;
}

export function updatePathInputDisplay(state: WorkspaceState, elements: WorkspaceElements) {
    if (!elements.pathInput) return;
    const prefix = getPathPrefix(state);
    elements.pathInput.value = `${prefix}...`;
}

function truncateBreadcrumbTitle(title: string): string {
    const chars = Array.from(title || '');
    if (chars.length <= MAX_BREADCRUMB_LABEL_CHARS) return title;
    return `${chars.slice(0, MAX_BREADCRUMB_LABEL_CHARS - 3).join('')}...`;
}

function appendBreadcrumbSeparator(elements: WorkspaceElements) {
    const separator = document.createElement('span');
    separator.className = 'breadcrumb-separator';
    separator.textContent = '/';
    separator.setAttribute('aria-hidden', 'true');
    elements.breadcrumb.appendChild(separator);
}

function appendBreadcrumbItem(
    elements: WorkspaceElements,
    item: BreadcrumbEntry,
    isCurrent: boolean,
    navigateToFolder: (id: string, title: string) => Promise<void>
) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'breadcrumb-item';
    button.textContent = truncateBreadcrumbTitle(item.title);
    button.title = item.title;
    button.dataset.id = item.id;
    if (isCurrent) {
        button.setAttribute('aria-current', 'page');
    }
    button.addEventListener('click', () => navigateToFolder(item.id, item.title));
    elements.breadcrumb.appendChild(button);
}

function appendBreadcrumbOverflow(
    state: WorkspaceState,
    elements: WorkspaceElements,
    hiddenItems: BreadcrumbEntry[],
    navigateToFolder: (id: string, title: string) => Promise<void>
) {
    const button = document.createElement('button');
    const hiddenPath = hiddenItems.map(item => item.title).join(' / ');
    button.type = 'button';
    button.className = 'breadcrumb-overflow-btn';
    button.textContent = '...';
    button.title = hiddenPath ? `Show hidden folders: ${hiddenPath}` : 'Show full path';
    button.setAttribute('aria-label', `Show ${hiddenItems.length} hidden breadcrumb item${hiddenItems.length === 1 ? '' : 's'}`);
    button.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        renderBreadcrumb(state, elements, navigateToFolder, true);
        window.requestAnimationFrame(() => {
            elements.breadcrumb.scrollLeft = elements.breadcrumb.scrollWidth;
        });
    });
    elements.breadcrumb.appendChild(button);
}

export function renderBreadcrumb(
    state: WorkspaceState,
    elements: WorkspaceElements,
    navigateToFolder: (id: string, title: string) => Promise<void>,
    expanded = false
) {
    const path = state.breadcrumbPath;
    const shouldCompress = !expanded && path.length > MAX_VISIBLE_BREADCRUMB_ITEMS;
    const hiddenItems = shouldCompress ? path.slice(1, -TRAILING_BREADCRUMB_ITEMS) : [];
    const tailItems = shouldCompress ? path.slice(-TRAILING_BREADCRUMB_ITEMS) : path.slice(1);

    elements.breadcrumb.innerHTML = '';
    elements.breadcrumb.classList.toggle('breadcrumb--compressed', shouldCompress);
    elements.breadcrumb.classList.toggle('breadcrumb--expanded', expanded);

    if (path.length === 0) return;

    appendBreadcrumbItem(elements, path[0], path.length === 1, navigateToFolder);

    if (shouldCompress) {
        appendBreadcrumbSeparator(elements);
        appendBreadcrumbOverflow(state, elements, hiddenItems, navigateToFolder);
    }

    tailItems.forEach((p) => {
        appendBreadcrumbSeparator(elements);
        appendBreadcrumbItem(elements, p, p.id === path[path.length - 1].id, navigateToFolder);
    });
}

export async function navigateToFolder(
    state: WorkspaceState,
    elements: WorkspaceElements,
    id: string,
    title: string,
    refreshNodes: (parentId: string) => Promise<void>
) {
    state.currentParentId = id;
    // Update breadcrumb
    if (id === 'root') {
        state.breadcrumbPath = [{id: 'root', title: getRootLabel(state)}];
    } else {
        // Simple logic: if exists in path, truncate, else append
        const index = state.breadcrumbPath.findIndex(p => p.id === id);
        if (index !== -1) {
            state.breadcrumbPath = state.breadcrumbPath.slice(0, index + 1);
        } else {
            state.breadcrumbPath.push({id, title});
        }
    }
    renderBreadcrumb(state, elements, (id, title) => navigateToFolder(state, elements, id, title, refreshNodes));
    await refreshNodes(id);
    updatePathInputDisplay(state, elements);
}

export function shakePathInput(elements: WorkspaceElements) {
    if (!elements.pathInput) return;
    elements.pathInput.classList.remove('path-input-shake');
    // Trigger reflow to restart animation
    void elements.pathInput.offsetWidth;
    elements.pathInput.classList.add('path-input-shake');
}

export async function resolvePath(
    state: WorkspaceState,
    elements: WorkspaceElements,
    rawPath: string,
    options: {
        onOpenStudy?: (studyId: string, context: { mode: WorkspaceMode; topFolder: string | null }) => void;
        onWorkspaceNavigate?: (mode: WorkspaceMode, topFolder: string | null) => void;
    },
    navigateToFolder: (id: string, title: string) => Promise<void>
) {
    let cleaned = rawPath.trim().replace(/\/+/g, '/');
    if (cleaned.endsWith('/...')) {
        cleaned = cleaned.slice(0, -4);
    }
    const rootPrefixes = ['root/', 'public/', 'shared/'];
    if (cleaned.endsWith('/') && !rootPrefixes.includes(cleaned)) {
        cleaned = cleaned.slice(0, -1);
    }
    if (!cleaned) return;
    const parts = cleaned.split('/').filter(Boolean);
    const prefixLabelMap: Record<string, string> = { root: 'Root', public: 'Public', shared: 'Shared' };
    if (parts.length === 0 || !prefixLabelMap[parts[0]]) {
        shakePathInput(elements);
        return;
    }
    if (parts.length === 1) {
        navigateToFolder('root', prefixLabelMap[parts[0]]);
        return;
    }

    const listEndpointMap: Record<string, string> = {
        root: '/api/v1/workspace/nodes',
        public: '/api/v1/workspace/public-nodes',
        shared: '/api/v1/workspace/shared-nodes',
    };
    const listEndpoint = listEndpointMap[parts[0]] ?? '/api/v1/workspace/nodes';

    let parentId = 'root';
    for (let i = 1; i < parts.length; i += 1) {
        const segment = parts[i];
        const isLast = i === parts.length - 1;
        const wantsStudy = isLast && segment.endsWith('.study');
        const name = wantsStudy ? segment.slice(0, -6) : segment;
        if (!name) {
            shakePathInput(elements);
            return;
        }

        const response = await api.get(`${listEndpoint}?parent_id=${parentId}`);
        const nodes = (response?.nodes || []) as any[];
        const match = nodes.find((node) => node.title === name);
        if (!match) {
            shakePathInput(elements);
            return;
        }

        if (!isLast) {
            if (match.node_type !== 'folder') {
                shakePathInput(elements);
                return;
            }
            parentId = match.id;
            continue;
        }

        if (wantsStudy) {
            if (match.node_type !== 'study') {
                shakePathInput(elements);
                return;
            }
            const modeMap: Record<string, WorkspaceMode> = { root: 'private', public: 'public', shared: 'shared' };
            const mode = modeMap[parts[0]] || 'private';
            const topFolderName = parts.length > 2 ? parts[1] : null;
            if (options.onOpenStudy) {
                options.onOpenStudy(match.id, { mode, topFolder: topFolderName });
            } else {
                window.location.assign(`/workspace/${match.id}`);
            }
            return;
        }

        if (match.node_type !== 'folder') {
            shakePathInput(elements);
            return;
        }
        navigateToFolder(match.id, match.title);
        return;
    }
}

export async function fetchFolderOptions() {
    const folders: Array<{ id: string; label: string; path: string }> = [];
    const walk = async (parentId: string, prefix: string) => {
        const response = await api.get(`/api/v1/workspace/nodes?parent_id=${parentId}`);
        const nodes = response.nodes as any[];
        const sorted = nodes.filter(n => n.node_type === 'folder');
        for (const node of sorted) {
            const label = prefix ? `${prefix} / ${node.title}` : node.title;
            folders.push({ id: node.id, label, path: node.path });
            await walk(node.id, label);
        }
    };
    await walk('root', 'Root');
    return [{ id: 'root', label: 'Root', path: '/root/' }, ...folders];
}
