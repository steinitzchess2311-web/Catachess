import React, { useRef, useEffect } from 'react';
import {
  ArchiveIcon,
  Cross2Icon,
  FileTextIcon,
  Link2Icon,
  MoveIcon,
  Pencil2Icon,
} from '@radix-ui/react-icons';
import './Dialog.css';
import './NodeActionsModal.css';

interface NodeActionsModalProps {
  node: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    version: number;
    parent_id: string | null;
    created_at: string;
    updated_at: string;
  };
  onClose: () => void;
  onMove: (node: any) => void;
  onRename: (node: any) => void;
  onDelete: (node: any) => void;
  onShare: (node: any) => void;
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const year = date.getFullYear();
  return `${month}/${day}/${year}`;
};

const NodeActionsModal: React.FC<NodeActionsModalProps> = ({
  node,
  onClose,
  onMove,
  onRename,
  onDelete,
  onShare,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const handleAction = (action: 'move' | 'rename' | 'delete' | 'share') => {
    if (action === 'move')   onMove(node);
    if (action === 'rename') onRename(node);
    if (action === 'delete') onDelete(node);
    if (action === 'share')  onShare(node);
  };

  const typeLabel = node.node_type === 'folder' ? 'Folder' : 'Study';
  const renderNodeIcon = () => {
    if (node.node_type === 'folder') {
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
        </svg>
      );
    }
    return <FileTextIcon width="18" height="18" aria-hidden="true" />;
  };

  return (
    <div className="cc-dialog-overlay node-actions-overlay">
      <div ref={modalRef} className="cc-dialog-card cc-dialog-card--compact node-actions-card" role="dialog" aria-modal="true" aria-labelledby="node-actions-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon cc-dialog-icon--neutral">{renderNodeIcon()}</span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">{typeLabel}</p>
              <h3 id="node-actions-title" className="cc-dialog-title">{node.title}</h3>
              <p className="cc-dialog-subtitle">
                Modified {formatDate(node.updated_at)}
              </p>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body node-actions-body">
          <div className="node-actions-meta">
            <span>Created {formatDate(node.created_at)}</span>
            <span>Updated {formatDate(node.updated_at)}</span>
          </div>
          <button
            className="cc-dialog-action-btn"
            onClick={() => handleAction('share')}
          >
            <Link2Icon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Share</span>
          </button>
          <button
            className="cc-dialog-action-btn"
            onClick={() => handleAction('move')}
          >
            <MoveIcon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Move</span>
          </button>
          <button
            className="cc-dialog-action-btn"
            onClick={() => handleAction('rename')}
          >
            <Pencil2Icon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Rename</span>
          </button>
          <button
            className="cc-dialog-action-btn cc-dialog-action-btn--danger"
            onClick={() => handleAction('delete')}
          >
            <ArchiveIcon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Move to Recycle</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodeActionsModal;
