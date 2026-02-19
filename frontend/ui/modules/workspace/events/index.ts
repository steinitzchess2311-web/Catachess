// Main integration module - coordinates all workspace modules
// LEGACY: This workspace module is deprecated. All study functionality has been moved to /patch/

import { WorkspaceOptions } from './types';
import { api } from '../../../assets/api';
import { createInitialState, setMode } from './state';
import { createModalRoots } from './modals';
import { renderReactComponents } from './rendering';
import { setupEventHandlers } from './eventHandlers';
import { extractElements, initializeToFolder } from './initialization';
import { createReactRoots } from './reactComponents';
import { createOrchestrator } from './orchestrator';
import { getRootLabel } from './navigation';

export async function initWorkspace(container: HTMLElement, options: WorkspaceOptions = {}) {
    // 1. Load template
    const template = document.getElementById('workspace-template') as HTMLTemplateElement;
    if (!template) return;
    container.appendChild(document.importNode(template.content, true));

    // 2. Extract elements
    const elements = extractElements(container);

    // 3. Initialize state
    const startParentId = options.initialParentId || 'root';
    const state = createInitialState(startParentId);

    // Apply initial mode (updates state.mode + root breadcrumb label)
    if (options.initialMode) {
        setMode(state, options.initialMode);
    }

    // 4. Create roots
    const modalRoots = createModalRoots();
    const reactRoots = createReactRoots();

    // 5. Create orchestrator (coordinates all modules)
    const { handlers, renderSortTogglesWrapper } = createOrchestrator(
        container,
        state,
        elements,
        options,
        modalRoots,
        reactRoots
    );

    // 6. Setup event handlers
    setupEventHandlers(state, elements, options, {
        openCreateModal: handlers.openCreateModalWrapper,
        navigateToFolder: handlers.navigateToFolder,
        renderItems: handlers.renderItems,
        refreshNodes: handlers.refreshNodes
    });

    // 7. Render static React components
    renderReactComponents(container);

    // 8. Initial render
    renderSortTogglesWrapper();

    // 9. Initialize to folder
    if (options.initialTopFolderName) {
        // Navigate to the named top-level folder (from URL slug)
        try {
            const response = await api.get('/api/v1/workspace/nodes?parent_id=root');
            const slug = options.initialTopFolderName!;
            const folder = (response.nodes as any[])?.find(
                (n) => n.node_type === 'folder' && (
                    n.title === slug ||
                    n.title === slug.replace(/-/g, ' ')
                )
            );
            if (folder) {
                await handlers.navigateToFolder(folder.id, folder.title);
            } else {
                await handlers.navigateToFolder('root', getRootLabel(state));
            }
        } catch {
            await handlers.navigateToFolder('root', getRootLabel(state));
        }
    } else {
        await initializeToFolder(
            state,
            elements,
            startParentId,
            handlers.navigateToFolder,
            handlers.refreshNodes
        );
    }
}
