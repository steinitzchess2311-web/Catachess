import React, { useState, useRef, useEffect } from 'react';
import { api } from '@ui/assets/api';
import './CreateModal.css';

interface CreateModalProps {
  isOpen: boolean;
  type: 'folder' | 'study';
  currentParentId: string;
  onClose: () => void;
  onSuccess: () => void;
}

function CreateNodeIcon({ type }: { type: 'folder' | 'study' }) {
  if (type === 'folder') {
    return (
      <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
        <path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
      <path fill="currentColor" d="M16 6a4 4 0 1 1-8 0a4 4 0 0 1 8 0M12 11c-2.5 0-5 1.5-5 4v1h10v-1c0-2.5-2.5-4-5-4m-6 7h12v2H6z" />
    </svg>
  );
}

const CreateModal: React.FC<CreateModalProps> = ({
  isOpen,
  type,
  currentParentId,
  onClose,
  onSuccess,
}) => {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Handle click outside to close
  useEffect(() => {
    if (!isOpen) return;

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
  }, [isOpen, onClose]);

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const validateTitle = (value: string): boolean => {
    if (!value.trim()) {
      setError('Title is required');
      return false;
    }
    if (value.includes('/')) {
      setError('No "/" in study or folder name');
      return false;
    }
    setError('');
    return true;
  };

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setTitle(value);
    if (error) {
      validateTitle(value);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateTitle(title)) {
      return;
    }

    setIsCreating(true);

    try {
      await api.post('/api/v1/workspace/nodes', {
        node_type: type,
        title: title.trim(),
        parent_id: currentParentId === 'root' ? null : currentParentId,
        visibility: 'private',
      });

      onSuccess();
      setTitle('');
      setError('');
    } catch (err: any) {
      console.error('Failed to create node:', err);
      setError(err?.message || 'Creation failed. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  if (!isOpen) return null;

  const modalTitle = type === 'folder' ? 'Create New Folder' : 'Create New Study';

  return (
    <div className="create-modal-overlay">
      <div ref={modalRef} className="create-modal-card">
        <div className="create-modal-header">
          <div className={`create-modal-icon ${type === 'study' ? 'is-study' : 'is-folder'}`}>
            <CreateNodeIcon type={type} />
          </div>
          <h3 className="create-modal-title">{modalTitle}</h3>
          <button className="create-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="create-modal-body">
          <div className="create-modal-form-group">
            <label htmlFor="create-title" className="create-modal-label">
              Title
            </label>
            <input
              ref={inputRef}
              id="create-title"
              type="text"
              className="create-modal-input"
              placeholder={`Enter ${type} name`}
              value={title}
              onChange={handleTitleChange}
              disabled={isCreating}
            />
            {error && <div className="create-modal-error">{error}</div>}
          </div>

          <div className="create-modal-footer">
            <button
              type="button"
              className="create-modal-btn create-modal-btn-cancel"
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="create-modal-btn create-modal-btn-create"
              disabled={isCreating || !title.trim()}
            >
              {isCreating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateModal;
