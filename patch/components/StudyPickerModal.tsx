import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';
import type { StudyTree } from '@patch/tree/type';

interface PickerNode {
  id: string;
  title: string;
  node_type: 'folder' | 'study' | 'workspace';
}

interface BreadcrumbItem {
  id: string;  // 'root' for top level
  title: string;
}

interface StudyPickerModalProps {
  currentTree: StudyTree;
  onClose: () => void;
  onNavigate: (studyId: string) => void;
}

const patchBase = '/api/v1/workspace/studies/study-patch';

export function StudyPickerModal({ currentTree, onClose, onNavigate }: StudyPickerModalProps) {
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([{ id: 'root', title: 'root' }]);
  const [nodes, setNodes] = useState<PickerNode[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNewStudyInput, setShowNewStudyInput] = useState(false);
  const [newStudyTitle, setNewStudyTitle] = useState('');
  const newStudyInputRef = useRef<HTMLInputElement | null>(null);

  const currentParentId = breadcrumbs[breadcrumbs.length - 1].id;

  const fetchNodes = useCallback(async (parentId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const param = parentId === 'root' ? 'root' : parentId;
      const response = await api.get(`/api/v1/workspace/nodes?parent_id=${param}`);
      const rawNodes: PickerNode[] = (response?.nodes || response || []).filter(
        (n: PickerNode) => n.node_type === 'folder' || n.node_type === 'study'
      );
      setNodes(rawNodes);
    } catch (e) {
      setError('Failed to load folders. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNodes(currentParentId);
  }, [currentParentId, fetchNodes]);

  useEffect(() => {
    if (showNewStudyInput && newStudyInputRef.current) {
      newStudyInputRef.current.focus();
      newStudyInputRef.current.select();
    }
  }, [showNewStudyInput]);

  const navigateInto = useCallback((node: PickerNode) => {
    setBreadcrumbs((prev) => [...prev, { id: node.id, title: node.title }]);
    setShowNewStudyInput(false);
    setNewStudyTitle('');
  }, []);

  const navigateToBreadcrumb = useCallback((index: number) => {
    setBreadcrumbs((prev) => prev.slice(0, index + 1));
    setShowNewStudyInput(false);
    setNewStudyTitle('');
  }, []);

  const sendToStudy = useCallback(async (studyId: string) => {
    setIsSending(true);
    setError(null);
    try {
      const now = new Date();
      const chapterTitle = `Analysis ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
      const chapter = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, {
        title: chapterTitle,
      });
      await api.put(`${patchBase}/chapter/${chapter.id}/tree`, currentTree);
      onNavigate(studyId);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send analysis to study.');
      setIsSending(false);
    }
  }, [currentTree, onNavigate]);

  const handleNodeClick = useCallback((node: PickerNode) => {
    if (node.node_type === 'folder') {
      navigateInto(node);
    } else if (node.node_type === 'study') {
      sendToStudy(node.id);
    }
  }, [navigateInto, sendToStudy]);

  const handleCreateNewStudy = useCallback(async () => {
    const title = newStudyTitle.trim();
    if (!title) return;
    if (title.includes('/')) {
      setError('Study name cannot contain "/"');
      return;
    }

    setIsSending(true);
    setError(null);
    try {
      const parentId = currentParentId === 'root' ? null : currentParentId;
      const newNode = await api.post('/api/v1/workspace/nodes', {
        node_type: 'study',
        title,
        parent_id: parentId,
        visibility: 'private',
      });
      await sendToStudy(newNode.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create study.');
      setIsSending(false);
    }
  }, [currentParentId, newStudyTitle, sendToStudy]);

  const handleOverlayClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  return (
    <div className="picker-overlay" onClick={handleOverlayClick}>
      <div className="picker-modal">
        <div className="picker-header">
          <h3>Send to Study</h3>
          <button type="button" className="picker-close-btn" onClick={onClose}>×</button>
        </div>

        {/* Breadcrumb */}
        <div className="picker-breadcrumb">
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.id}>
              {index > 0 && <span className="picker-breadcrumb-sep">/</span>}
              <span
                className={`picker-breadcrumb-item${index === breadcrumbs.length - 1 ? ' current' : ''}`}
                onClick={() => index < breadcrumbs.length - 1 && navigateToBreadcrumb(index)}
              >
                {crumb.title}
              </span>
            </React.Fragment>
          ))}
        </div>

        {/* Node list */}
        <div className="picker-body">
          {isLoading && <div className="picker-loading">Loading...</div>}
          {!isLoading && nodes.length === 0 && (
            <div className="picker-empty">No folders or studies here.</div>
          )}
          {!isLoading && nodes.length > 0 && (
            <ul className="picker-node-list">
              {nodes.map((node) => (
                <li
                  key={node.id}
                  className={`picker-node-item${node.node_type === 'study' ? ' is-study' : ''}`}
                  onClick={() => !isSending && handleNodeClick(node)}
                >
                  <span className="picker-node-icon">
                    {node.node_type === 'folder' ? '📁' : '♟'}
                  </span>
                  <span className="picker-node-title">{node.title}</span>
                  {node.node_type === 'study' && (
                    <span style={{ fontSize: 12, color: '#888', flexShrink: 0 }}>
                      {isSending ? 'Sending...' : 'Click to add chapter'}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {error && <div className="picker-error">{error}</div>}

        {/* Footer: new study */}
        <div className="picker-footer">
          {showNewStudyInput ? (
            <div className="picker-new-study-row">
              <input
                ref={newStudyInputRef}
                className="picker-new-study-input"
                type="text"
                placeholder="Study title..."
                value={newStudyTitle}
                onChange={(e) => setNewStudyTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreateNewStudy();
                  if (e.key === 'Escape') {
                    setShowNewStudyInput(false);
                    setNewStudyTitle('');
                  }
                }}
              />
              <button
                type="button"
                className="picker-btn secondary"
                onClick={() => { setShowNewStudyInput(false); setNewStudyTitle(''); }}
                disabled={isSending}
              >
                Cancel
              </button>
              <button
                type="button"
                className="picker-btn primary"
                onClick={handleCreateNewStudy}
                disabled={isSending || !newStudyTitle.trim()}
              >
                {isSending ? 'Creating...' : 'Create & Add'}
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="picker-btn secondary"
              onClick={() => setShowNewStudyInput(true)}
              disabled={isSending}
            >
              + New Study here
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default StudyPickerModal;
