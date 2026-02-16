// Main integration module - coordinates all workspace modules
// LEGACY: This workspace module is deprecated. All study functionality has been moved to /patch/

import { WorkspaceOptions } from './types';
import { createInitialState, setSortSettings } from './state';
import { createModalRoots } from './modals';
import { renderReactComponents } from './rendering';
import { setupEventHandlers } from './eventHandlers';
import { extractElements, initializeToFolder } from './initialization';
import { createReactRoots } from './reactComponents';
import { createOrchestrator } from './orchestrator';

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
    await initializeToFolder(
        state,
        elements,
        startParentId,
        handlers.navigateToFolder,
        handlers.refreshNodes
    );
}
