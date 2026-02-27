/**
 * WorkspaceShareModal
 * ───────────────────
 * Student picks a workspace node (study or folder) to share with the teacher
 * via the classroom "Share to Teacher" action.
 *
 * Browsing logic mirrors StudyPickerModal (same workspace /nodes API).
 * The action on selecting a study/folder is "share to teacher" instead of
 * "send to study". Folders navigate deeper; studies/other nodes trigger sharing.
 *
 * NOTE: This is separate from the legacy StudyPickerModal (analysis → send to study).
 * Both are kept independently — they serve different purposes.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@ui/assets/api';
import { shareToTeacher } from '../api';

interface PickerNode {
  id: string;
  title: string;
  node_type: 'folder' | 'study';
}

interface BreadcrumbItem {
  id: string;
  title: string;
}

interface Props {
  classroomId: string;
  onClose: () => void;
  /** Called after a successful share, with the shared node's title. */
  onShared: (nodeTitle: string) => void;
}

function FolderIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
      <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
    </svg>
  );
}

function StudyIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3a3 3 0 110 6 3 3 0 010-6zm4 11H8v-.5c0-2 2-3 4-3s4 1 4 3v.5z" />
    </svg>
  );
}

export const WorkspaceShareModal: React.FC<Props> = ({ classroomId, onClose, onShared }) => {
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: 'root', title: 'My Workspace' },
  ]);
  const [nodes, setNodes] = useState<PickerNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [sharing, setSharing] = useState<string | null>(null); // node_id currently being shared
  const [error, setError] = useState<string | null>(null);

  const currentParentId = breadcrumbs[breadcrumbs.length - 1].id;

  // ── Fetch workspace nodes ────────────────────────────────────────────────

  const fetchNodes = useCallback(async (parentId: string) => {
    setLoading(true);
    setError(null);
    try {
      const param = parentId === 'root' ? 'root' : parentId;
      const response = await api.get(`/api/v1/workspace/nodes?parent_id=${param}`);
      const raw: PickerNode[] = (response?.nodes ?? response ?? []).filter(
        (n: PickerNode) => n.node_type === 'folder' || n.node_type === 'study',
      );
      setNodes(raw);
    } catch {
      setError('Failed to load workspace. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNodes(currentParentId);
  }, [currentParentId, fetchNodes]);

  // ── Navigation ───────────────────────────────────────────────────────────

  const navigateInto = useCallback((node: PickerNode) => {
    setBreadcrumbs(prev => [...prev, { id: node.id, title: node.title }]);
  }, []);

  const navigateToBreadcrumb = useCallback((index: number) => {
    setBreadcrumbs(prev => prev.slice(0, index + 1));
  }, []);

  // ── Share action ─────────────────────────────────────────────────────────

  const handleShare = useCallback(
    async (node: PickerNode) => {
      if (sharing) return;
      setSharing(node.id);
      setError(null);
      try {
        await shareToTeacher(classroomId, node.id);
        onShared(node.title);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to share. Please try again.');
        setSharing(null);
      }
    },
    [classroomId, sharing, onShared],
  );

  const handleNodeClick = useCallback(
    (node: PickerNode) => {
      if (sharing) return;
      if (node.node_type === 'folder') {
        navigateInto(node);
      } else {
        handleShare(node);
      }
    },
    [sharing, navigateInto, handleShare],
  );

  // ── Overlay close ────────────────────────────────────────────────────────

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <div className="picker-overlay" onClick={handleOverlayClick}>
      <div className="picker-modal">

        {/* Header */}
        <div className="picker-header">
          <h3>Share to Teacher</h3>
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
          {loading && <div className="picker-loading">Loading...</div>}

          {!loading && nodes.length === 0 && (
            <div className="picker-empty">No folders or studies here.</div>
          )}

          {!loading && nodes.length > 0 && (
            <ul className="picker-node-list">
              {nodes.map(node => (
                <li
                  key={node.id}
                  className={`picker-node-item${node.node_type === 'study' ? ' is-study' : ''}${sharing === node.id ? ' is-sending' : ''}`}
                  onClick={() => handleNodeClick(node)}
                  style={{ cursor: sharing ? 'not-allowed' : 'pointer', opacity: sharing && sharing !== node.id ? 0.5 : 1 }}
                >
                  <span className={`picker-node-icon ${node.node_type === 'study' ? 'is-study' : 'is-folder'}`}>
                    {node.node_type === 'folder' ? <FolderIcon /> : <StudyIcon />}
                  </span>
                  <span className="picker-node-title">{node.title}</span>
                  {node.node_type === 'study' && (
                    <span className="picker-node-hint">
                      {sharing === node.id ? 'Sharing…' : 'Click to share'}
                    </span>
                  )}
                  {node.node_type === 'folder' && (
                    <span className="picker-node-hint" style={{ color: 'var(--cl-text-muted)' }}>
                      Open →
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Error */}
        {error && <div className="picker-error">{error}</div>}

        {/* Footer hint */}
        <div className="picker-footer">
          <p style={{ fontSize: '0.8rem', color: 'var(--cl-text-secondary)', margin: 0 }}>
            Select a study to share with your teacher. Your teacher will see it in their workspace
            with viewer access. You keep full edit access.
          </p>
        </div>

      </div>
    </div>
  );
};
