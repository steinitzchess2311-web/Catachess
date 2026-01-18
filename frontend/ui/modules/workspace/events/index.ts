import { api } from '../../../assets/api';
import { makeDraggable } from '../../../core/drag';

type WorkspaceOptions = {
    onOpenStudy?: (studyId: string) => void;
};

export async function initWorkspace(container: HTMLElement, options: WorkspaceOptions = {}) {
    // 1. Load Workspace Template
    const template = document.getElementById('workspace-template') as HTMLTemplateElement;
    if (!template) return;
    const content = document.importNode(template.content, true);
    container.appendChild(content);

    // 2. Select Core Elements
    const itemsGrid = container.querySelector('#items-grid') as HTMLElement;
    const breadcrumb = container.querySelector('#breadcrumb') as HTMLElement;
    const folderTree = container.querySelector('#folder-tree') as HTMLElement;
    const newBtn = container.querySelector('#new-btn') as HTMLButtonElement;

    // State
    let currentParentId = 'root';
    let breadcrumbPath: Array<{id: string, title: string}> = [{id: 'root', title: 'Root'}];

    // 3. Helper Functions

    // Fetch and render nodes for current folder
    const refreshNodes = async (parentId: string) => {
        try {
            // Using the new unified list endpoint
            const response = await api.get(`/api/v1/workspace/nodes?parent_id=${parentId}`);
            renderItems(response.nodes);
        } catch (error) {
            console.error('Failed to fetch nodes:', error);
        }
    };

    const renderItems = (nodes: any[]) => {
        itemsGrid.innerHTML = '';
        const folderTpl = document.getElementById('folder-item-template') as HTMLTemplateElement;
        const studyTpl = document.getElementById('study-item-template') as HTMLTemplateElement;

        nodes.forEach(node => {
            const tpl = node.node_type === 'folder' ? folderTpl : studyTpl;
            const item = document.importNode(tpl.content, true);
            const itemDiv = item.querySelector('.grid-item') as HTMLElement;
            itemDiv.setAttribute('data-id', node.id);
            itemDiv.setAttribute('data-type', node.node_type);
            itemDiv.setAttribute('data-version', String(node.version));
            itemDiv.setAttribute('data-parent-id', node.parent_id ?? '');
            itemDiv.querySelector('.item-title')!.textContent = node.title;
            
            const date = new Date(node.updated_at).toLocaleDateString();
            itemDiv.querySelector('.item-meta')!.textContent = date;

            itemDiv.addEventListener('click', () => {
                if (node.node_type === 'folder') {
                    navigateToFolder(node.id, node.title);
                    return;
                }
                if (options.onOpenStudy) {
                    options.onOpenStudy(node.id);
                } else {
                    window.location.assign(`/workspace/${node.id}`);
                }
            });

            itemDiv.addEventListener('contextmenu', (event) => {
                event.preventDefault();
                openNodeActions(node);
            });

            itemsGrid.appendChild(item);
        });
    };

    const navigateToFolder = (id: string, title: string) => {
        currentParentId = id;
        // Update breadcrumb
        if (id === 'root') {
            breadcrumbPath = [{id: 'root', title: 'Root'}];
        } else {
            // Simple logic: if exists in path, truncate, else append
            const index = breadcrumbPath.findIndex(p => p.id === id);
            if (index !== -1) {
                breadcrumbPath = breadcrumbPath.slice(0, index + 1);
            } else {
                breadcrumbPath.push({id, title});
            }
        }
        renderBreadcrumb();
        refreshNodes(id);
    };

    const renderBreadcrumb = () => {
        breadcrumb.innerHTML = '';
        breadcrumbPath.forEach((p, index) => {
            const span = document.createElement('span');
            span.className = 'breadcrumb-item';
            span.textContent = p.title;
            span.addEventListener('click', () => navigateToFolder(p.id, p.title));
            breadcrumb.appendChild(span);
        });
    };

    const mountModal = (templateId: string) => {
        const tpl = document.getElementById(templateId) as HTMLTemplateElement;
        const modal = document.importNode(tpl.content, true);
        const overlay = modal.querySelector('.modal-overlay') as HTMLElement;
        const card = overlay.querySelector('.modal-card') as HTMLElement;
        const closeBtns = overlay.querySelectorAll('.modal-close');
        document.body.appendChild(overlay);
        makeDraggable(card, { handle: '.modal-header' });
        const close = () => overlay.remove();
        closeBtns.forEach(btn => btn.addEventListener('click', close));
        return { overlay, close };
    };

    const fetchFolderOptions = async () => {
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
    };

    const openMoveModal = async (node: any) => {
        const { overlay, close } = mountModal('move-node-template');
        const select = overlay.querySelector('#move-destination') as HTMLSelectElement;
        const confirmBtn = overlay.querySelector('#confirm-move') as HTMLButtonElement;
        const optionsList = await fetchFolderOptions();
        optionsList.forEach(option => {
            if (node.node_type === 'folder' && option.path.startsWith(node.path)) {
                return;
            }
            const opt = document.createElement('option');
            opt.value = option.id;
            opt.textContent = option.label;
            select.appendChild(opt);
        });

        confirmBtn.addEventListener('click', async () => {
            const newParentId = select.value === 'root' ? null : select.value;
            try {
                await api.post(`/api/v1/workspace/nodes/${node.id}/move`, {
                    new_parent_id: newParentId,
                    version: node.version,
                });
                close();
                refreshNodes(currentParentId);
            } catch (error) {
                console.error('Failed to move node:', error);
                alert('Move failed');
            }
        });
    };

    const openDeleteConfirm = (node: any) => {
        const { overlay, close } = mountModal('delete-confirm-template');
        const confirmBtn = overlay.querySelector('#confirm-delete') as HTMLButtonElement;
        confirmBtn.addEventListener('click', async () => {
            try {
                await api.delete(`/api/v1/workspace/nodes/${node.id}/purge?version=${node.version}`);
                close();
                refreshNodes(currentParentId);
            } catch (error) {
                console.error('Failed to delete node:', error);
                alert('Delete failed');
            }
        });
    };

    const openNodeActions = (node: any) => {
        const { overlay } = mountModal('node-actions-template');
        const title = overlay.querySelector('.modal-title') as HTMLElement;
        const eyebrow = overlay.querySelector('.modal-eyebrow') as HTMLElement;
        title.textContent = node.title;
        eyebrow.textContent = node.node_type === 'folder' ? 'Folder' : 'Study';
        const actions = overlay.querySelectorAll('.action-btn');
        actions.forEach(btn => {
            btn.addEventListener('click', async () => {
                const action = (btn as HTMLButtonElement).dataset.action;
                if (action === 'move') {
                    overlay.remove();
                    await openMoveModal(node);
                }
                if (action === 'delete') {
                    overlay.remove();
                    openDeleteConfirm(node);
                }
            });
        });
    };

    // Modal Handling
    const openCreateModal = () => {
        const modalTpl = document.getElementById('create-modal-template') as HTMLTemplateElement;
        const modal = document.importNode(modalTpl.content, true);
        const overlay = modal.querySelector('.modal-overlay') as HTMLElement;
        const card = overlay.querySelector('.modal-card') as HTMLElement;
        const closeBtns = overlay.querySelectorAll('.modal-close');
        const confirmBtn = overlay.querySelector('#confirm-create') as HTMLButtonElement;
        const typeSelect = overlay.querySelector('#new-type') as HTMLSelectElement;
        const titleInput = overlay.querySelector('#new-title') as HTMLInputElement;

        document.body.appendChild(overlay);

        // Make draggable
        makeDraggable(card, { handle: '.modal-header' });

        const close = () => overlay.remove();
        closeBtns.forEach(btn => btn.addEventListener('click', close));

        confirmBtn.addEventListener('click', async () => {
            const title = titleInput.value;
            const type = typeSelect.value;
            if (!title) return;

            try {
                // POST /api/v1/workspace/nodes
                await api.post('/api/v1/workspace/nodes', {
                    node_type: type,
                    title: title,
                    parent_id: currentParentId === 'root' ? null : currentParentId,
                    visibility: 'private'
                });
                close();
                refreshNodes(currentParentId);
            } catch (error) {
                console.error('Failed to create node:', error);
                alert('Creation failed');
            }
        });
    };

    // 4. Initial Bindings
    newBtn.addEventListener('click', openCreateModal);

    // Initial load
    navigateToFolder('root', 'Root');
}
