import React, { useState, useRef, useEffect } from 'react';
import { Cross2Icon, FileTextIcon, Pencil2Icon } from '@radix-ui/react-icons';
import { api } from '@ui/assets/api';
import './Dialog.css';
import './RenameModal.css';

interface RenameModalProps {
  node: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    version: number;
  };
  onClose: () => void;
  onSuccess: () => void;
}

const RenameModal: React.FC<RenameModalProps> = ({ node, onClose, onSuccess }) => {
  const [inputValue, setInputValue] = useState(node.title);
  const [error, setError] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input on mount
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, []);

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

  // Validate input
  const validate = (): boolean => {
    const trimmed = inputValue.trim();

    if (!trimmed) {
      setError('Name cannot be empty');
      return false;
    }

    if (trimmed.includes('/')) {
      setError('Name cannot contain "/"');
      return false;
    }

    setError('');
    return true;
  };

  // Handle rename with retry logic for version conflicts
  const handleRename = async () => {
    if (!validate()) return;

    setIsRenaming(true);
    setError('');

    const trimmed = inputValue.trim();

    try {
      // First attempt
      await api.put(`/api/v1/workspace/nodes/${node.id}`, {
        title: trimmed,
        version: node.version,
      });

      onSuccess();
    } catch (error: any) {
      // Handle version conflict (409) with retry
      if (error?.status === 409) {
        console.log('[RenameModal] Version conflict detected, refreshing and retrying...');

        try {
          // Fetch latest version
          const refreshed = await api.get(`/api/v1/workspace/nodes/${node.id}`);

          // Retry with new version
          await api.put(`/api/v1/workspace/nodes/${node.id}`, {
            title: trimmed,
            version: refreshed.version,
          });

          console.log('[RenameModal] Rename succeeded after version refresh');
          onSuccess();
        } catch (retryError: any) {
          console.error('[RenameModal] Failed to rename after retry:', retryError);
          setError('Rename failed. Please try again.');
          setIsRenaming(false);
        }
      } else {
        console.error('[RenameModal] Failed to rename:', error);
        setError(error?.message || 'Rename failed. Please try again.');
        setIsRenaming(false);
      }
    }
  };

  // Handle enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isRenaming) {
      handleRename();
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
    <div className="cc-dialog-overlay rename-modal-overlay">
      <div ref={modalRef} className="cc-dialog-card rename-modal-card" role="dialog" aria-modal="true" aria-labelledby="rename-modal-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon">
              <Pencil2Icon width="18" height="18" aria-hidden="true" />
            </span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Workspace</p>
              <h3 id="rename-modal-title" className="cc-dialog-title">Rename</h3>
              <p className="cc-dialog-subtitle">{node.title}</p>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body">
          <label className="cc-dialog-label">
            {typeLabel} name
          </label>
          <div className="rename-modal-input-row">
            <span className="rename-modal-node-icon">{renderNodeIcon()}</span>
            <input
              ref={inputRef}
              type="text"
              className="cc-dialog-input rename-modal-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isRenaming}
            />
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
            disabled={isRenaming}
          >
            Cancel
          </button>
          <button
            className="cc-dialog-button cc-dialog-button--primary"
            onClick={handleRename}
            disabled={isRenaming}
          >
            {isRenaming ? 'Renaming...' : 'Rename'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RenameModal;
