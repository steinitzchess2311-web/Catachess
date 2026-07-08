import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Cross2Icon, MoveIcon } from '@radix-ui/react-icons';
import FolderTree from './FolderTree';
import { FolderNode, fetchFolders, resolvePathToId } from '../../utils/folderTree';
import { api } from '@ui/assets/api';
import './Dialog.css';
import './MoveModal.css';

interface MoveModalProps {
  node: {
    id: string;
    title: string;
    node_type: 'folder' | 'study';
    version: number;
    parent_id: string | null;
    path?: string;
  };
  onClose: () => void;
  onSuccess: () => void;
}

const MoveModal: React.FC<MoveModalProps> = ({ node, onClose, onSuccess }) => {
  const [inputValue, setInputValue] = useState('root/');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [rootFolders, setRootFolders] = useState<FolderNode[]>([]);
  const [isMoving, setIsMoving] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load root folders on mount
  useEffect(() => {
    fetchFolders('root', 'root').then(setRootFolders);
  }, []);

  // Shake input on invalid path
  const shakeInput = () => {
    if (!inputRef.current) return;
    inputRef.current.classList.remove('shake');
    // Trigger reflow to restart animation
    void inputRef.current.offsetWidth;
    inputRef.current.classList.add('shake');
    setTimeout(() => {
      inputRef.current?.classList.remove('shake');
    }, 300);
  };

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

  const handleInputFocus = () => {
    setIsDropdownOpen(true);
  };

  const handleInputBlur = (e: React.FocusEvent) => {
    // Check if clicking inside dropdown
    if (modalRef.current?.contains(e.relatedTarget as Node)) {
      return;
    }
    // Delay to allow click events to fire
    setTimeout(() => {
      setIsDropdownOpen(false);
    }, 200);
  };

  const handleSelectFolder = useCallback((folder: FolderNode) => {
    console.log('[MoveModal] Folder selected:', folder.title, 'path:', folder.path);
    setInputValue(folder.path);
    setIsDropdownOpen(false);
    inputRef.current?.blur();
    console.log('[MoveModal] Input value set to:', folder.path);
  }, []);

  const handleMove = async () => {
    setIsMoving(true);

    try {
      // Allow empty input or "root" or "Root" to move to root folder
      const trimmedInput = inputValue.trim();
      const normalizedInput = trimmedInput.toLowerCase();

      let targetFolderId: string | null = 'root';

      // If input is not empty and not just "root", resolve the path
      if (trimmedInput && normalizedInput !== 'root' && normalizedInput !== 'root/') {
        targetFolderId = await resolvePathToId(inputValue);

        if (!targetFolderId) {
          shakeInput();
          setIsMoving(false);
          return;
        }
      }

      // Prevent moving folder into itself or its descendants
      if (node.node_type === 'folder' && node.path && inputValue && inputValue.startsWith(node.path)) {
        shakeInput();
        setIsMoving(false);
        return;
      }

      await api.post(`/api/v1/workspace/nodes/${node.id}/move`, {
        new_parent_id: targetFolderId === 'root' ? null : targetFolderId,
        version: node.version,
      });

      onSuccess();
    } catch (error) {
      console.error('Failed to move node:', error);
      alert('Move failed. Please try again.');
      setIsMoving(false);
    }
  };

  // Extract search term from input (last segment after /)
  const searchTerm = useMemo(() => {
    const parts = inputValue.split('/').filter(Boolean);
    if (parts.length <= 1) return '';
    return parts[parts.length - 1];
  }, [inputValue]);

  return (
    <div className="cc-dialog-overlay move-modal-overlay">
      <div ref={modalRef} className="cc-dialog-card move-modal-card" role="dialog" aria-modal="true" aria-labelledby="move-modal-title">
        <div className="cc-dialog-header">
          <div className="cc-dialog-heading">
            <span className="cc-dialog-icon">
              <MoveIcon width="18" height="18" aria-hidden="true" />
            </span>
            <div className="cc-dialog-title-block">
              <p className="cc-dialog-kicker">Workspace</p>
              <h3 id="move-modal-title" className="cc-dialog-title">Move item</h3>
              <p className="cc-dialog-subtitle">{node.title}</p>
            </div>
          </div>
          <button type="button" className="cc-dialog-close" onClick={onClose} aria-label="Close">
            <Cross2Icon width="16" height="16" />
          </button>
        </div>

        <div className="cc-dialog-body move-modal-body">
          <label className="cc-dialog-label">Destination folder</label>
          <input
            ref={inputRef}
            type="text"
            className="cc-dialog-input move-modal-input"
            value={inputValue}
            onChange={(e) => {
              const newValue = e.target.value;
              // Ensure "root/" prefix cannot be deleted
              if (newValue.startsWith('root/')) {
                setInputValue(newValue);
              } else {
                setInputValue('root/');
              }
            }}
            onKeyDown={(e) => {
              // Prevent deleting "root/" prefix
              const input = e.currentTarget;
              const cursorPos = input.selectionStart || 0;
              const isDeleting = e.key === 'Backspace' || e.key === 'Delete';

              if (isDeleting && cursorPos <= 5) {
                e.preventDefault();
              }
            }}
            onSelect={(e) => {
              // Prevent cursor from moving before "root/"
              const input = e.currentTarget;
              const cursorPos = input.selectionStart || 0;

              if (cursorPos < 5) {
                input.setSelectionRange(5, 5);
              }
            }}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
          />

          {isDropdownOpen && (
            <div className="folder-dropdown">
              <FolderTree
                folders={rootFolders}
                onSelectFolder={handleSelectFolder}
                filterText={searchTerm}
              />
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

export default MoveModal;
