import React, { useState, useRef, useEffect } from 'react';
import { ArchiveIcon, Cross2Icon, ExclamationTriangleIcon, FileTextIcon } from '@radix-ui/react-icons';
import { api } from '@ui/assets/api';
import './Dialog.css';
import './DeleteModal.css';

interface DeleteModalProps {
  node: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    version: number;
  };
  onClose: () => void;
  onSuccess: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({ node, onClose, onSuccess }) => {
  const [isDeleting, setIsDeleting] = useState(false);
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

  // Handle move to recycle bin with retry logic for version conflicts
  const handleDelete = async () => {
    setIsDeleting(true);
    setError('');

    try {
      await api.delete(`/api/v1/workspace/nodes/${node.id}?version=${node.version}`);
      onSuccess();
    } catch (error: any) {
      if (error?.status === 409) {
        try {
          const refreshed = await api.get(`/api/v1/workspace/nodes/${node.id}`);
          await api.delete(`/api/v1/workspace/nodes/${refreshed.id}?version=${refreshed.version}`);
          onSuccess();
        } catch (retryError: any) {
          setError('Move to Recycle failed. Please try again.');
          setIsDeleting(false);
        }
      } else {
        setError(error?.message || 'Move to Recycle failed. Please try again.');
        setIsDeleting(false);
      }
    }
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
    <div className="cc-dialog-overlay delete-modal-overlay">
      <div ref={modalRef} className="cc-dialog-card delete-modal-card" role="dialog" aria-modal="true" aria-labelledby="delete-modal-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon cc-dialog-icon--danger">
              <ArchiveIcon width="18" height="18" aria-hidden="true" />
            </span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Recycle bin</p>
              <h3 id="delete-modal-title" className="cc-dialog-title">Move to recycle</h3>
              <p className="cc-dialog-subtitle">{node.title}</p>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body delete-modal-body">
          <div className="delete-modal-warning">
            <div className="cc-dialog-object">
              {renderNodeIcon()}
              <span className="cc-dialog-object-title">{node.title}</span>
            </div>
            <p className="delete-modal-hint cc-dialog-note">
              This {typeLabel.toLowerCase()} will move to the recycle bin. You can restore it later.
            </p>
          </div>
          {error && (
            <div className="cc-dialog-error">
              <ExclamationTriangleIcon width="14" height="14" aria-hidden="true" />
              {error}
            </div>
          )}
        </div>

        <div className="cc-dialog-footer">
          <button
            className="cc-dialog-button"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            className="cc-dialog-button cc-dialog-button--danger"
            onClick={handleDelete}
            disabled={isDeleting}
          >
            {isDeleting ? 'Moving...' : 'Move to Recycle'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteModal;
