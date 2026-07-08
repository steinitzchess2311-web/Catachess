import React, { useRef, useEffect } from 'react';
import { Cross2Icon, FileTextIcon, ResetIcon, TrashIcon } from '@radix-ui/react-icons';
import './Dialog.css';
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

  const typeLabel = node.node_type === 'folder' ? 'Folder' : 'Study';
  const deletedDate = node.deleted_at ? new Date(node.deleted_at).toLocaleDateString() : '';
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
      <div ref={modalRef} className="cc-dialog-card cc-dialog-card--compact node-actions-card" role="dialog" aria-modal="true" aria-labelledby="trash-actions-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon cc-dialog-icon--neutral">{renderNodeIcon()}</span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">{typeLabel} in recycle</p>
              <h3 id="trash-actions-title" className="cc-dialog-title">{node.title}</h3>
              {deletedDate && <p className="cc-dialog-subtitle">Deleted {deletedDate}</p>}
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body node-actions-body">
          <button
            className="cc-dialog-action-btn"
            onClick={() => onRecover(node)}
          >
            <ResetIcon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Recover</span>
          </button>
          <button
            className="cc-dialog-action-btn cc-dialog-action-btn--danger"
            onClick={() => onDeleteForever(node)}
          >
            <TrashIcon width="17" height="17" aria-hidden="true" />
            <span className="action-label">Delete forever</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default TrashActionsModal;
