// Modal management for all dialogs

import React from 'react';
import ReactDOM from 'react-dom/client';
import CreateModal from '../../../../web/src/components/dialogBox/CreateModal';
import NodeActionsModal from '../../../../web/src/components/dialogBox/NodeActionsModal';
import NodeShareModal from '../../../../web/src/components/dialogBox/NodeShareModal';
import MoveModal from '../../../../web/src/components/dialogBox/MoveModal';
import RenameModal from '../../../../web/src/components/dialogBox/RenameModal';
import DeleteModal from '../../../../web/src/components/dialogBox/DeleteModal';
import DragMoveModal from '../../../../web/src/components/dialogBox/DragMoveModal';
import { ModalRoots } from './types';

export function createModalRoots(): ModalRoots {
    return {
        modalContainer: null,
        modalRoot: null,
        actionsModalContainer: null,
        actionsModalRoot: null,
        moveModalContainer: null,
        moveModalRoot: null,
        renameModalContainer: null,
        renameModalRoot: null,
        deleteModalContainer: null,
        deleteModalRoot: null,
        dragMoveModalContainer: null,
        dragMoveModalRoot: null,
        shareModalContainer: null,
        shareModalRoot: null,
    };
}

export function openCreateModal(
    modalRoots: ModalRoots,
    type: 'folder' | 'study',
    currentParentId: string,
    onSuccess: () => void
) {
    // Create modal container if not exists
    if (!modalRoots.modalContainer) {
        modalRoots.modalContainer = document.createElement('div');
        modalRoots.modalContainer.id = 'create-modal-root';
        document.body.appendChild(modalRoots.modalContainer);
        modalRoots.modalRoot = ReactDOM.createRoot(modalRoots.modalContainer);
    }

    // Render modal
    modalRoots.modalRoot!.render(
        React.createElement(CreateModal, {
            isOpen: true,
            type: type,
            currentParentId: currentParentId,
            onClose: () => {
                // Unmount modal
                if (modalRoots.modalRoot) {
                    modalRoots.modalRoot.render(null);
                }
            },
            onSuccess: () => {
                // Unmount modal
                if (modalRoots.modalRoot) {
                    modalRoots.modalRoot.render(null);
                }
                onSuccess();
            }
        })
    );
}

export function openMoveModal(
    modalRoots: ModalRoots,
    node: any,
    onSuccess: () => void
) {
    // Create move modal container if not exists
    if (!modalRoots.moveModalContainer) {
        modalRoots.moveModalContainer = document.createElement('div');
        modalRoots.moveModalContainer.id = 'move-modal-root';
        document.body.appendChild(modalRoots.moveModalContainer);
        modalRoots.moveModalRoot = ReactDOM.createRoot(modalRoots.moveModalContainer);
    }

    // Render MoveModal React component
    modalRoots.moveModalRoot!.render(
        React.createElement(MoveModal, {
            node: node,
            onClose: () => {
                // Unmount modal
                if (modalRoots.moveModalRoot) {
                    modalRoots.moveModalRoot.render(null);
                }
            },
            onSuccess: () => {
                // Unmount modal
                if (modalRoots.moveModalRoot) {
                    modalRoots.moveModalRoot.render(null);
                }
                onSuccess();
            }
        })
    );
}

export function openDeleteConfirm(
    modalRoots: ModalRoots,
    node: any,
    onSuccess: () => void
) {
    // Create delete modal container if not exists
    if (!modalRoots.deleteModalContainer) {
        modalRoots.deleteModalContainer = document.createElement('div');
        modalRoots.deleteModalContainer.id = 'delete-modal-root';
        document.body.appendChild(modalRoots.deleteModalContainer);
        modalRoots.deleteModalRoot = ReactDOM.createRoot(modalRoots.deleteModalContainer);
    }

    // Render React DeleteModal
    modalRoots.deleteModalRoot!.render(
        React.createElement(DeleteModal, {
            node: node,
            onClose: () => {
                // Unmount modal
                if (modalRoots.deleteModalRoot) {
                    modalRoots.deleteModalRoot.render(null);
                }
            },
            onSuccess: () => {
                // Unmount modal
                if (modalRoots.deleteModalRoot) {
                    modalRoots.deleteModalRoot.render(null);
                }
                onSuccess();
            }
        })
    );
}

export function openMoveConfirm(
    modalRoots: ModalRoots,
    source: any,
    target: any,
    onSuccess: () => void
) {
    // Create drag move modal container if not exists
    if (!modalRoots.dragMoveModalContainer) {
        modalRoots.dragMoveModalContainer = document.createElement('div');
        modalRoots.dragMoveModalContainer.id = 'drag-move-modal-root';
        document.body.appendChild(modalRoots.dragMoveModalContainer);
        modalRoots.dragMoveModalRoot = ReactDOM.createRoot(modalRoots.dragMoveModalContainer);
    }

    // Render DragMoveModal React component
    modalRoots.dragMoveModalRoot!.render(
        React.createElement(DragMoveModal, {
            sourceNode: source,
            targetNode: target,
            onClose: () => {
                // Unmount modal
                if (modalRoots.dragMoveModalRoot) {
                    modalRoots.dragMoveModalRoot.render(null);
                }
            },
            onSuccess: () => {
                // Unmount modal
                if (modalRoots.dragMoveModalRoot) {
                    modalRoots.dragMoveModalRoot.render(null);
                }
                onSuccess();
            }
        })
    );
}

export function openRenameModal(
    modalRoots: ModalRoots,
    node: any,
    onSuccess: () => void
) {
    // Create rename modal container if not exists
    if (!modalRoots.renameModalContainer) {
        modalRoots.renameModalContainer = document.createElement('div');
        modalRoots.renameModalContainer.id = 'rename-modal-root';
        document.body.appendChild(modalRoots.renameModalContainer);
        modalRoots.renameModalRoot = ReactDOM.createRoot(modalRoots.renameModalContainer);
    }

    // Render React RenameModal
    modalRoots.renameModalRoot!.render(
        React.createElement(RenameModal, {
            node: node,
            onClose: () => {
                // Unmount modal
                if (modalRoots.renameModalRoot) {
                    modalRoots.renameModalRoot.render(null);
                }
            },
            onSuccess: () => {
                // Unmount modal
                if (modalRoots.renameModalRoot) {
                    modalRoots.renameModalRoot.render(null);
                }
                onSuccess();
            }
        })
    );
}

export function openShareModal(
    modalRoots: ModalRoots,
    node: any,
) {
    if (!modalRoots.shareModalContainer) {
        modalRoots.shareModalContainer = document.createElement('div');
        modalRoots.shareModalContainer.id = 'share-modal-root';
        document.body.appendChild(modalRoots.shareModalContainer);
        modalRoots.shareModalRoot = ReactDOM.createRoot(modalRoots.shareModalContainer);
    }

    modalRoots.shareModalRoot!.render(
        React.createElement(NodeShareModal, {
            node,
            onClose: () => {
                if (modalRoots.shareModalRoot) {
                    modalRoots.shareModalRoot.render(null);
                }
            },
        })
    );
}

export function openNodeActions(
    modalRoots: ModalRoots,
    node: any,
    onMove: (n: any) => void,
    onRename: (n: any) => void,
    onDelete: (n: any) => void,
    onShare: (n: any) => void,
    disabledActions?: { move?: boolean; rename?: boolean; delete?: boolean }
) {
    // Create actions modal container if not exists
    if (!modalRoots.actionsModalContainer) {
        modalRoots.actionsModalContainer = document.createElement('div');
        modalRoots.actionsModalContainer.id = 'node-actions-modal-root';
        document.body.appendChild(modalRoots.actionsModalContainer);
        modalRoots.actionsModalRoot = ReactDOM.createRoot(modalRoots.actionsModalContainer);
    }

    // Render NodeActionsModal React component
    modalRoots.actionsModalRoot!.render(
        React.createElement(NodeActionsModal, {
            node: node,
            disabledActions,
            onClose: () => {
                if (modalRoots.actionsModalRoot) {
                    modalRoots.actionsModalRoot.render(null);
                }
            },
            onMove: (n: any) => {
                if (modalRoots.actionsModalRoot) {
                    modalRoots.actionsModalRoot.render(null);
                }
                onMove(n);
            },
            onRename: (n: any) => {
                if (modalRoots.actionsModalRoot) {
                    modalRoots.actionsModalRoot.render(null);
                }
                onRename(n);
            },
            onDelete: (n: any) => {
                if (modalRoots.actionsModalRoot) {
                    modalRoots.actionsModalRoot.render(null);
                }
                onDelete(n);
            },
            onShare: (n: any) => {
                if (modalRoots.actionsModalRoot) {
                    modalRoots.actionsModalRoot.render(null);
                }
                onShare(n);
            },
        })
    );
}
