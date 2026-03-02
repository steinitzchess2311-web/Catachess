/**
 * WorkspacePicker
 * ───────────────
 * Reusable workspace browser for selecting a folder or study.
 *
 * UX:
 *  - Folders: click row body → navigate inside; right-side action button → select the folder
 *  - Studies: click anywhere → onSelect
 *  - Breadcrumb navigation, loading & empty states
 *
 * Extracted from WorkspaceShareModal so it can be reused in
 * CreateAssignmentModal (material picker) and other contexts.
 *
 * Uses inline styles + cl-* CSS variables (classroom design system).
 */

import React, { useCallback, useEffect, useState } from 'react';
import { api } from '@ui/assets/api';

export interface PickerNode {
  id: string;
  title: string;
  node_type: 'folder' | 'study';
}

interface BreadcrumbItem {
  id: string;
  title: string;
}

export interface WorkspacePickerProps {
  /** Which node types can be selected. Default: both. */
  selectable?: ('folder' | 'study')[];
  /** Called when the user selects a node. */
  onSelect: (node: PickerNode) => void;
  /** Close the picker (overlay click / × button). */
  onClose: () => void;
  /** Modal title. Default: "Select from Workspace" */
  title?: string;
  /** Action button label. Default: "Select" */
  selectLabel?: string;
  /** Show a loading state on a specific node (e.g. while sharing). */
  busyNodeId?: string | null;
}

// ── Icons ─────────────────────────────────────────────────────────────────────

const FolderIcon = () => (
  <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path d="M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
  </svg>
);

const StudyIcon = () => (
  <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 3a3 3 0 110 6 3 3 0 010-6zm4 11H8v-.5c0-2 2-3 4-3s4 1 4 3v.5z" />
  </svg>
);

// ── Component ─────────────────────────────────────────────────────────────────

export const WorkspacePicker: React.FC<WorkspacePickerProps> = ({
  selectable = ['folder', 'study'],
  onSelect,
  onClose,
  title = 'Select from Workspace',
  selectLabel = 'Select',
  busyNodeId = null,
}) => {
  const [breadcrumbs, setBreadcrumbs] = useState<BreadcrumbItem[]>([
    { id: 'root', title: 'My Workspace' },
  ]);
  const [nodes, setNodes] = useState<PickerNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectableSet = new Set(selectable);
  const currentParentId = breadcrumbs[breadcrumbs.length - 1].id;

  // ── Fetch ───────────────────────────────────────────────────────────────

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

  // ── Navigation ──────────────────────────────────────────────────────────

  const navigateInto = useCallback((node: PickerNode) => {
    setBreadcrumbs(prev => [...prev, { id: node.id, title: node.title }]);
  }, []);

  const navigateToBreadcrumb = useCallback((index: number) => {
    setBreadcrumbs(prev => prev.slice(0, index + 1));
  }, []);

  const handleOverlayClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  }, [onClose]);

  // ── Render ──────────────────────────────────────────────────────────────

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
        onClick={e => e.stopPropagation()}
        style={{
          background: 'var(--cl-bg, #fff)',
          border: '1.5px solid var(--cl-border, #e2e8f0)',
          borderRadius: 12,
          width: 440,
          maxWidth: '92vw',
          maxHeight: '72vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '0.9rem 1.1rem 0.7rem',
          borderBottom: '1px solid var(--cl-border, #e2e8f0)',
        }}>
          <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>{title}</h3>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: '1.3rem', lineHeight: 1,
              color: 'var(--cl-text-secondary, #64748b)', padding: '0 2px',
            }}
          >×</button>
        </div>

        {/* Breadcrumb */}
        <div style={{
          padding: '0.45rem 1.1rem',
          fontSize: '0.78rem',
          color: 'var(--cl-text-secondary, #64748b)',
          borderBottom: '1px solid var(--cl-border, #e2e8f0)',
          display: 'flex', flexWrap: 'wrap', gap: '2px', alignItems: 'center',
        }}>
          {breadcrumbs.map((crumb, index) => (
            <React.Fragment key={crumb.id}>
              {index > 0 && <span style={{ opacity: 0.4, margin: '0 1px' }}>/</span>}
              <span
                onClick={() => index < breadcrumbs.length - 1 && navigateToBreadcrumb(index)}
                style={{
                  cursor: index < breadcrumbs.length - 1 ? 'pointer' : 'default',
                  fontWeight: index === breadcrumbs.length - 1 ? 600 : 400,
                  color: index < breadcrumbs.length - 1
                    ? 'var(--cl-accent, #3b82f6)' : 'inherit',
                  textDecoration: index < breadcrumbs.length - 1 ? 'underline' : 'none',
                }}
              >
                {crumb.title}
              </span>
            </React.Fragment>
          ))}
        </div>

        {/* Node list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loading && (
            <p style={{ padding: '1rem 1.1rem', margin: 0, fontSize: '0.85rem', color: 'var(--cl-text-secondary, #64748b)' }}>
              Loading…
            </p>
          )}
          {!loading && nodes.length === 0 && (
            <p style={{ padding: '1rem 1.1rem', margin: 0, fontSize: '0.85rem', color: 'var(--cl-text-muted, #94a3b8)' }}>
              No folders or studies here.
            </p>
          )}
          {!loading && nodes.map(node => {
            const isFolder = node.node_type === 'folder';
            const isSelectable = selectableSet.has(node.node_type);
            const isBusy = busyNodeId === node.id;

            return (
              <div
                key={node.id}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.55rem',
                  padding: '0.5rem 1.1rem',
                  opacity: busyNodeId && !isBusy ? 0.45 : 1,
                  transition: 'background 0.1s',
                }}
                className="cl-ws-picker-row"
              >
                {/* Left: icon + name */}
                <div
                  onClick={() => {
                    if (busyNodeId) return;
                    if (isFolder && !isSelectable) navigateInto(node);
                    else if (isFolder) navigateInto(node);
                    else if (isSelectable) onSelect(node);
                  }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                    flex: 1, minWidth: 0,
                    cursor: busyNodeId ? 'not-allowed' : 'pointer',
                  }}
                >
                  <span style={{ color: isFolder ? 'var(--cl-accent, #3b82f6)' : 'var(--cl-text-secondary, #64748b)', flexShrink: 0 }}>
                    {isFolder ? <FolderIcon /> : <StudyIcon />}
                  </span>
                  <span style={{
                    fontSize: '0.875rem', fontWeight: 500,
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {node.title}
                  </span>
                  {isFolder && (
                    <span style={{ fontSize: '0.72rem', color: 'var(--cl-text-muted, #94a3b8)', flexShrink: 0 }}>
                      Open →
                    </span>
                  )}
                </div>

                {/* Right: action button */}
                {isSelectable && (
                  <button
                    type="button"
                    onClick={() => !busyNodeId && onSelect(node)}
                    disabled={!!busyNodeId}
                    title={`${selectLabel} "${node.title}"`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.3rem',
                      fontSize: '0.75rem', fontWeight: 500,
                      padding: '0.25rem 0.6rem',
                      borderRadius: 6,
                      border: '1px solid var(--cl-border, #e2e8f0)',
                      background: isBusy ? 'var(--cl-surface, #f8fafc)' : 'transparent',
                      color: isBusy
                        ? 'var(--cl-text-muted, #94a3b8)'
                        : 'var(--cl-accent, #3b82f6)',
                      cursor: busyNodeId ? 'not-allowed' : 'pointer',
                      flexShrink: 0,
                      transition: 'background 0.1s, color 0.1s',
                    }}
                  >
                    {isBusy ? 'Working…' : selectLabel}
                  </button>
                )}
              </div>
            );
          })}
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

        {/* Footer hint */}
        <div style={{
          padding: '0.6rem 1.1rem',
          borderTop: '1px solid var(--cl-border, #e2e8f0)',
          fontSize: '0.77rem',
          color: 'var(--cl-text-muted, #94a3b8)',
        }}>
          Click <strong>{selectLabel}</strong> to pick a node. Click a folder name to browse inside.
        </div>
      </div>
    </div>
  );
};
