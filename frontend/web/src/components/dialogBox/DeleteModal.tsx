import React, { useState, useRef, useEffect } from 'react';
import { api } from '@ui/assets/api';
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

  const icon = node.node_type === 'folder' ? '📁' : '📖';
  const typeLabel = node.node_type === 'folder' ? 'Folder' : 'Study';

  return (
    <div className="delete-modal-overlay">
      <div ref={modalRef} className="delete-modal-card">
        <div className="delete-modal-header">
          <h3 className="delete-modal-title">
            🗑️ Move to Recycle
          </h3>
          <button className="delete-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="delete-modal-body">
          <div className="delete-modal-warning">
            <p className="delete-modal-message">
              Move this {typeLabel.toLowerCase()} to Recycle Bin?
            </p>
            <div className="delete-modal-node-info">
              {icon} <strong>{node.title}</strong>
            </div>
            <p className="delete-modal-hint">
              You can restore it from the Recycle Bin.
            </p>
          </div>
          {error && (
            <div className="delete-modal-error">
              {error}
            </div>
          )}
        </div>

        <div className="delete-modal-footer">
          <button
            className="delete-modal-btn delete-modal-btn-cancel"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            className="delete-modal-btn delete-modal-btn-delete"
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
