/**
 * WorkspaceShareModal
 * ───────────────────
 * Student picks a workspace node (study or folder) to share with the teacher
 * via the classroom "Share to Teacher" action.
 *
 * NOTE: Uses inline styles + cl-* classes (classroom design system) intentionally —
 * this component lives in the classroom module which does not import analysis.css.
 * The legacy StudyPickerModal (analysis → send to study) is kept as-is.
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
  /** Called after a successful share with the shared node's title. */
  onShared: (nodeTitle: string) => void;
}

// ── Icons ────────────────────────────────────────────────────────────────────

function FolderIcon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
    </svg>
  );
}

function StudyIcon() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3a3 3 0 110 6 3 3 0 010-6zm4 11H8v-.5c0-2 2-3 4-3s4 1 4 3v.5z" />
    </svg>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export const WorkspaceShareModal: React.FC<Props> = ({ classroomId, onClose, onShared }) => {
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: 'root', title: 'My Workspace' },
  ]);
  const [nodes, setNodes] = useState<PickerNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [sharing, setSharing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const currentParentId = breadcrumbs[breadcrumbs.length - 1].id;

  // ── Fetch ─────────────────────────────────────────────────────────────────

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

  useEffect(() => { fetchNodes(currentParentId); }, [currentParentId, fetchNodes]);

  // ── Navigation ────────────────────────────────────────────────────────────

  const navigateInto = useCallback((node: PickerNode) => {
    setBreadcrumbs(prev => [...prev, { id: node.id, title: node.title }]);
  }, []);

  const navigateToBreadcrumb = useCallback((index: number) => {
    setBreadcrumbs(prev => prev.slice(0, index + 1));
  }, []);

  // ── Share ─────────────────────────────────────────────────────────────────

  const handleShare = useCallback(async (node: PickerNode) => {
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
  }, [classroomId, sharing, onShared]);

  const handleNodeClick = useCallback((node: PickerNode) => {
    if (sharing) return;
    if (node.node_type === 'folder') navigateInto(node);
    else handleShare(node);
  }, [sharing, navigateInto, handleShare]);

  const handleOverlayClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div
      onClick={handleOverlayClick}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: 'var(--cl-bg, #fff)',
          border: '1.5px solid var(--cl-border, #e2e8f0)',
          borderRadius: 12,
          width: 440,
          maxWidth: '92vw',
          maxHeight: '75vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '1rem 1.1rem 0.75rem',
          borderBottom: '1px solid var(--cl-border, #e2e8f0)',
        }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 700 }}>Share to Teacher</h3>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '1.3rem', lineHeight: 1, color: 'var(--cl-text-secondary, #64748b)',
              padding: '0 2px',
            }}
          >×</button>
        </div>

        {/* Breadcrumb */}
        <div style={{
          padding: '0.5rem 1.1rem',
          fontSize: '0.8rem',
          color: 'var(--cl-text-secondary, #64748b)',
          borderBottom: '1px solid var(--cl-border, #e2e8f0)',
          display: 'flex', flexWrap: 'wrap', gap: '0.15rem', alignItems: 'center',
        }}>
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.id}>
              {index > 0 && <span style={{ margin: '0 2px', opacity: 0.5 }}>/</span>}
              <span
                onClick={() => index < breadcrumbs.length - 1 && navigateToBreadcrumb(index)}
                style={{
                  cursor: index < breadcrumbs.length - 1 ? 'pointer' : 'default',
                  fontWeight: index === breadcrumbs.length - 1 ? 600 : 400,
                  color: index < breadcrumbs.length - 1 ? 'var(--cl-accent, #3b82f6)' : 'inherit',
                  textDecoration: index < breadcrumbs.length - 1 ? 'underline' : 'none',
                }}
              >
                {crumb.title}
              </span>
            </React.Fragment>
          ))}
        </div>

        {/* Node list */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem 0' }}>
          {loading && (
            <p style={{ padding: '1rem 1.1rem', margin: 0, color: 'var(--cl-text-secondary, #64748b)', fontSize: '0.85rem' }}>
              Loading…
            </p>
          )}
          {!loading && nodes.length === 0 && (
            <p style={{ padding: '1rem 1.1rem', margin: 0, color: 'var(--cl-text-muted, #94a3b8)', fontSize: '0.85rem' }}>
              No folders or studies here.
            </p>
          )}
          {!loading && nodes.map(node => (
            <div
              key={node.id}
              onClick={() => handleNodeClick(node)}
              style={{
                display: 'flex', alignItems: 'center', gap: '0.6rem',
                padding: '0.55rem 1.1rem',
                cursor: sharing ? 'not-allowed' : 'pointer',
                opacity: sharing && sharing !== node.id ? 0.45 : 1,
                background: sharing === node.id ? 'var(--cl-surface, #f8fafc)' : 'transparent',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => { if (!sharing) (e.currentTarget as HTMLDivElement).style.background = 'var(--cl-surface, #f8fafc)'; }}
              onMouseLeave={e => { if (sharing !== node.id) (e.currentTarget as HTMLDivElement).style.background = 'transparent'; }}
            >
              {/* Icon */}
              <span style={{ color: node.node_type === 'folder' ? 'var(--cl-accent, #3b82f6)' : 'var(--cl-text-secondary, #64748b)' }}>
                {node.node_type === 'folder' ? <FolderIcon /> : <StudyIcon />}
              </span>

              {/* Title */}
              <span style={{ fontSize: '0.875rem', fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {node.title}
              </span>

              {/* Action hint */}
              <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted, #94a3b8)', flexShrink: 0 }}>
                {node.node_type === 'folder'
                  ? 'Open →'
                  : sharing === node.id ? 'Sharing…' : 'Share'}
              </span>
            </div>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div style={{
            padding: '0.5rem 1.1rem',
            background: 'var(--cl-overdue-bg, #fef2f2)',
            color: 'var(--cl-overdue, #ef4444)',
            fontSize: '0.82rem',
            borderTop: '1px solid var(--cl-border, #e2e8f0)',
          }}>
            {error}
          </div>
        )}

        {/* Footer */}
        <div style={{
          padding: '0.65rem 1.1rem',
          borderTop: '1px solid var(--cl-border, #e2e8f0)',
          fontSize: '0.78rem',
          color: 'var(--cl-text-muted, #94a3b8)',
        }}>
          Select a study to share with your teacher. You keep full edit access.
        </div>
      </div>
    </div>
  );
};
