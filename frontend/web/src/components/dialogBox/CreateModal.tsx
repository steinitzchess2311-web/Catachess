import React, { useState, useRef, useEffect } from 'react';
import { Cross2Icon, FileTextIcon } from '@radix-ui/react-icons';
import { api } from '@ui/assets/api';
import './Dialog.css';
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
      <svg viewBox="0 0 24 24" width="19" height="19" aria-hidden="true">
        <path fill="currentColor" d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
      </svg>
    );
  }
  return <FileTextIcon width="19" height="19" aria-hidden="true" />;
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

  const modalTitle = type === 'folder' ? 'Create folder' : 'Create study';
  const objectLabel = type === 'folder' ? 'Folder name' : 'Study name';
  const placeholder = type === 'folder' ? 'Opening preparation' : 'King pawn repertoire';

  return (
    <div className="cc-dialog-overlay create-modal-overlay">
      <div ref={modalRef} className="cc-dialog-card create-modal-card" role="dialog" aria-modal="true" aria-labelledby="create-modal-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className={`cc-dialog-icon ${type === 'study' ? '' : 'cc-dialog-icon--neutral'}`}>
              <CreateNodeIcon type={type} />
            </span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Workspace</p>
              <h3 id="create-modal-title" className="cc-dialog-title">{modalTitle}</h3>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="cc-dialog-body">
            <label htmlFor="create-title" className="cc-dialog-label">
              {objectLabel}
            </label>
            <input
              ref={inputRef}
              id="create-title"
              type="text"
              className="cc-dialog-input create-modal-input"
              placeholder={placeholder}
              value={title}
              onChange={handleTitleChange}
              disabled={isCreating}
            />
            {error && <div className="cc-dialog-error">{error}</div>}
          </div>

          <div className="cc-dialog-footer">
            <button
              type="button"
              className="cc-dialog-button"
              onClick={onClose}
              disabled={isCreating}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="cc-dialog-button cc-dialog-button--primary"
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
