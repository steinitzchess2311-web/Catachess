// Type definitions for workspace module

export type WorkspaceOptions = {
    onOpenStudy?: (studyId: string, context: { mode: WorkspaceMode; topFolder: string | null }) => void;
    initialParentId?: string;
    initialMode?: WorkspaceMode;
    initialTopFolderName?: string;
    onWorkspaceNavigate?: (mode: WorkspaceMode, topFolder: string | null) => void;
};

export type SortKey = 'created' | 'modified' | null;
export type SortDir = 'asc' | 'desc';
export type WorkspaceMode = 'private' | 'public' | 'shared' | 'trash';

export interface WorkspaceState {
    currentParentId: string;
    breadcrumbPath: Array<{id: string, title: string}>;
    allNodesCache: any[] | null;
    dragNode: any | null;
    sortKey: SortKey;
    sortDir: SortDir;
    isBatchMode: boolean;
    selectedItemIds: Set<string>;
    currentNodes: any[];
    mode: WorkspaceMode;
    /** Offset for the next page of public-root nodes (infinite scroll) */
    publicOffset: number;
    /** Whether there are more public-root pages to load */
    publicHasMore: boolean;
}

export interface WorkspaceElements {
    container: HTMLElement;
    itemsGrid: HTMLElement;
    breadcrumb: HTMLElement;
    folderTree: HTMLElement;
    pathInput: HTMLInputElement | null;
    searchInput: HTMLInputElement;
    searchClearBtn: HTMLButtonElement;
    sidebarToggleBtn: HTMLButtonElement | null;
}

export interface ModalRoots {
    modalContainer: HTMLDivElement | null;
    modalRoot: any;
    actionsModalContainer: HTMLDivElement | null;
    actionsModalRoot: any;
    moveModalContainer: HTMLDivElement | null;
    moveModalRoot: any;
    renameModalContainer: HTMLDivElement | null;
    renameModalRoot: any;
    deleteModalContainer: HTMLDivElement | null;
    deleteModalRoot: any;
    dragMoveModalContainer: HTMLDivElement | null;
    dragMoveModalRoot: any;
    shareModalContainer: HTMLDivElement | null;
    shareModalRoot: any;
}
