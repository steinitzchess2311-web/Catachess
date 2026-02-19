import React, { useRef, useEffect } from 'react';
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

  const icon = node.node_type === 'folder' ? '📁' : '📖';
  const typeLabel = node.node_type === 'folder' ? 'Folder' : 'Study';

  return (
    <div className="node-actions-overlay">
      <div ref={modalRef} className="node-actions-card">
        <div className="node-actions-header">
          <h3 className="node-actions-title">
            {node.title}
            <div className="info-tooltip">
              <div className="tooltip-row">
                <span className="tooltip-icon">{icon}</span>
                <span className="tooltip-type">{typeLabel}</span>
              </div>
              <div className="tooltip-item">Created at: {formatDate(node.created_at)}</div>
              <div className="tooltip-item">Last modified: {formatDate(node.updated_at)}</div>
            </div>
          </h3>
          <button className="node-actions-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="node-actions-body">
          <button
            className="node-action-btn node-action-btn-share"
            onClick={() => handleAction('share')}
          >
            <span className="action-icon">🔗</span>
            <span className="action-label">Share</span>
          </button>
          <button
            className="node-action-btn"
            onClick={() => handleAction('move')}
          >
            <span className="action-icon">📦</span>
            <span className="action-label">Move</span>
          </button>
          <button
            className="node-action-btn"
            onClick={() => handleAction('rename')}
          >
            <span className="action-icon">✏️</span>
            <span className="action-label">Rename</span>
          </button>
          <button
            className="node-action-btn node-action-btn-danger"
            onClick={() => handleAction('delete')}
          >
            <span className="action-icon">🗑️</span>
            <span className="action-label">Delete</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodeActionsModal;
