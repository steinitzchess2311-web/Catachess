import React, { useState, useRef, useEffect } from 'react';
import { Cross2Icon, FileTextIcon, MoveIcon } from '@radix-ui/react-icons';
import { api } from '@ui/assets/api';
import './Dialog.css';
import './DragMoveModal.css';

interface DragMoveModalProps {
  sourceNode: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    version: number;
  };
  targetNode: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
  };
  onClose: () => void;
  onSuccess: () => void;
}

const DragMoveModal: React.FC<DragMoveModalProps> = ({ sourceNode, targetNode, onClose, onSuccess }) => {
  const [isMoving, setIsMoving] = useState(false);
  const [error, setError] = useState('');

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

  // Handle move
  const handleMove = async () => {
    setIsMoving(true);
    setError('');

    try {
      await api.post(`/api/v1/workspace/nodes/${sourceNode.id}/move`, {
        new_parent_id: targetNode.id,
        version: sourceNode.version,
      });

      onSuccess();
    } catch (error: any) {
      console.error('[DragMoveModal] Failed to move:', error);
      setError(error?.message || 'Move failed. Please try again.');
      setIsMoving(false);
    }
  };

  const renderIcon = (type: 'folder' | 'study') => {
    if (type === 'folder') {
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
        </svg>
      );
    }
    return <FileTextIcon width="18" height="18" aria-hidden="true" />;
  };

  return (
    <div className="cc-dialog-overlay drag-move-modal-overlay">
      <div ref={modalRef} className="cc-dialog-card drag-move-modal-card" role="dialog" aria-modal="true" aria-labelledby="drag-move-modal-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon">
              <MoveIcon width="18" height="18" aria-hidden="true" />
            </span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Workspace</p>
              <h3 id="drag-move-modal-title" className="cc-dialog-title">Move item</h3>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body drag-move-modal-body">
          <div className="drag-move-modal-confirmation">
            <p className="drag-move-modal-message cc-dialog-note">
              Move this item into the selected folder.
            </p>
            <div className="cc-dialog-object">
              {renderIcon(sourceNode.node_type)}
              <span className="cc-dialog-object-title">{sourceNode.title}</span>
            </div>
            <div className="drag-move-modal-arrow" aria-hidden="true">↓</div>
            <div className="cc-dialog-object">
              {renderIcon('folder')}
              <span className="cc-dialog-object-title">{targetNode.title}</span>
            </div>
          </div>
          {error && (
            <div className="cc-dialog-error">
              {error}
            </div>
          )}
        </div>

        <div className="cc-dialog-footer">
          <button
            className="cc-dialog-button"
            onClick={onClose}
            disabled={isMoving}
          >
            Cancel
          </button>
          <button
            className="cc-dialog-button cc-dialog-button--primary"
            onClick={handleMove}
            disabled={isMoving}
          >
            {isMoving ? 'Moving...' : 'Move'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DragMoveModal;
