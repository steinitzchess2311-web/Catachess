import React, { useRef, useEffect } from 'react';
import './NodeActionsModal.css';

interface TrashActionsModalProps {
  node: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    deleted_at?: string;
  };
  onClose: () => void;
  onRecover: (node: any) => void;
  onDeleteForever: (node: any) => void;
}

const TrashActionsModal: React.FC<TrashActionsModalProps> = ({
  node,
  onClose,
  onRecover,
  onDeleteForever,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    const id = setTimeout(() => document.addEventListener('mousedown', handleClickOutside), 0);
    return () => {
      clearTimeout(id);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const icon = node.node_type === 'folder' ? '📁' : '📖';
  const typeLabel = node.node_type === 'folder' ? 'Folder' : 'Study';
  const deletedDate = node.deleted_at ? new Date(node.deleted_at).toLocaleDateString() : '';

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
              {deletedDate && (
                <div className="tooltip-item">Deleted: {deletedDate}</div>
              )}
            </div>
          </h3>
          <button className="node-actions-close" onClick={onClose}>×</button>
        </div>

        <div className="node-actions-body">
          <button
            className="node-action-btn"
            style={{ borderColor: 'var(--primary)', color: 'var(--primary)' }}
            onClick={() => onRecover(node)}
          >
            <span className="action-icon">↩️</span>
            <span className="action-label">Recover</span>
          </button>
          <button
            className="node-action-btn node-action-btn-danger"
            onClick={() => onDeleteForever(node)}
          >
            <span className="action-icon">🗑️</span>
            <span className="action-label">Delete forever</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default TrashActionsModal;
