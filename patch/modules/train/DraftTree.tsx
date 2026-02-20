/**
 * DraftTree.tsx - Editable draft move tree for train mode.
 *
 * Mirrors MoveBranch/MoveItem pattern from movetree.tsx but with:
 * - Inline input at leaf nodes for adding moves
 * - Delete button per node
 * - Comment textarea per node
 * - Real-time move validation (green/red border)
 */

import React, { useState, useCallback, useRef } from 'react';
import type { DraftNode, UseDraftTreeReturn } from './useDraftTree';
import { validateMove } from '../../chessJS/replay';
import { getStartPlyFromFen } from './trainUtils';

// ─── MoveInput ────────────────────────────────────────────────────────────────

interface MoveInputProps {
  parentId: string;
  parentFen: string;
  onConfirm: (parentId: string, san: string) => { ok: boolean; san: string | null; error: string | null };
}

function MoveInput({ parentId, parentFen, onConfirm }: MoveInputProps) {
  const [value, setValue] = useState('');
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback((san: string) => {
    if (!san.trim()) {
      setIsValid(null);
      setErrorMsg(null);
      return;
    }
    const result = validateMove(parentFen, san.trim());
    setIsValid(result.valid);
    setErrorMsg(result.valid ? null : (result.error || 'Invalid move'));
  }, [parentFen]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    setValue(v);
    validate(v);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const trimmed = value.trim();
      if (!trimmed) return;
      const result = onConfirm(parentId, trimmed);
      if (result.ok) {
        setValue('');
        setIsValid(null);
        setErrorMsg(null);
      } else {
        setIsValid(false);
        setErrorMsg(result.error || 'Invalid move');
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setValue('');
      setIsValid(null);
      setErrorMsg(null);
    }
  };

  const borderColor = isValid === true ? '#16a34a' : isValid === false ? '#dc2626' : '#d1d5db';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="e.g. e4"
        title={errorMsg || 'Type a SAN move, press Enter to confirm'}
        style={{
          width: 72,
          padding: '2px 6px',
          fontSize: 12,
          borderRadius: 3,
          border: `1px solid ${borderColor}`,
          outline: 'none',
          fontFamily: 'monospace',
        }}
      />
      {errorMsg && (
        <span style={{ fontSize: 11, color: '#dc2626', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={errorMsg}>
          {errorMsg}
        </span>
      )}
    </div>
  );
}

// ─── DraftNodeItem ────────────────────────────────────────────────────────────

interface DraftNodeItemProps {
  nodeId: string;
  nodes: Record<string, DraftNode>;
  nodeFen: Map<string, string>;
  prefix: string;
  depth: number;
  onAddMove: (parentId: string, san: string) => { ok: boolean; san: string | null; error: string | null };
  onDelete: (nodeId: string) => void;
  onSetComment: (nodeId: string, comment: string) => void;
}

function DraftNodeItem({
  nodeId,
  nodes,
  nodeFen,
  prefix,
  depth,
  onAddMove,
  onDelete,
  onSetComment,
}: DraftNodeItemProps) {
  const node = nodes[nodeId];
  if (!node) return null;

  const [showComment, setShowComment] = useState(false);
  const currentFen = nodeFen.get(nodeId) ?? '';
  const isLeaf = node.children.length === 0;

  return (
    <div style={{ marginLeft: depth > 0 ? 12 : 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
        {/* Move badge */}
        <span
          style={{
            padding: '2px 6px',
            borderRadius: 3,
            backgroundColor: '#eff6ff',
            color: '#2563eb',
            fontWeight: 600,
            fontFamily: 'monospace',
            fontSize: 13,
            border: '1px solid #bfdbfe',
            whiteSpace: 'nowrap',
          }}
        >
          {prefix}{node.san}
        </span>

        {/* Comment toggle */}
        <button
          type="button"
          onClick={() => setShowComment((v) => !v)}
          title={showComment ? 'Hide comment' : 'Add/edit comment'}
          style={iconBtnStyle}
        >
          {node.comment ? '💬' : '+'}
        </button>

        {/* Delete button */}
        <button
          type="button"
          onClick={() => onDelete(nodeId)}
          title="Delete this move and subtree"
          style={{ ...iconBtnStyle, color: '#dc2626' }}
        >
          ×
        </button>
      </div>

      {/* Inline comment */}
      {showComment && (
        <textarea
          value={node.comment}
          onChange={(e) => onSetComment(nodeId, e.target.value)}
          placeholder="Add a comment..."
          rows={2}
          style={{
            marginTop: 4,
            width: '100%',
            maxWidth: 260,
            fontSize: 12,
            padding: '3px 6px',
            borderRadius: 3,
            border: '1px solid #d1d5db',
            resize: 'vertical',
          }}
        />
      )}

      {/* Children */}
      {node.children.map((childId, idx) => {
        const childNode = nodes[childId];
        if (!childNode) return null;
        const childPrefix = idx === 0 ? '' : '(var) ';
        return (
          <DraftNodeItem
            key={childId}
            nodeId={childId}
            nodes={nodes}
            nodeFen={nodeFen}
            prefix={childPrefix}
            depth={depth + 1}
            onAddMove={onAddMove}
            onDelete={onDelete}
            onSetComment={onSetComment}
          />
        );
      })}

      {/* Input at leaf nodes */}
      {isLeaf && currentFen && (
        <div style={{ marginLeft: depth > 0 ? 12 : 0, marginTop: 2 }}>
          <MoveInput
            parentId={nodeId}
            parentFen={currentFen}
            onConfirm={onAddMove}
          />
        </div>
      )}
    </div>
  );
}

const iconBtnStyle: React.CSSProperties = {
  padding: '1px 5px',
  border: '1px solid #d1d5db',
  borderRadius: 3,
  background: 'white',
  cursor: 'pointer',
  fontSize: 12,
  lineHeight: 1.4,
};

// ─── DraftTree (root) ─────────────────────────────────────────────────────────

export interface DraftTreeProps {
  draft: UseDraftTreeReturn;
}

export function DraftTree({ draft }: DraftTreeProps) {
  const { nodes, nodeFen, rootId, startFen, addMove, setComment, deleteNode } = draft;
  const root = nodes[rootId];
  const rootFen = nodeFen.get(rootId) ?? startFen;
  const startPly = getStartPlyFromFen(startFen);

  if (!root) return null;

  // Root has no SAN — show inline input for first move
  const hasChildren = root.children.length > 0;

  return (
    <div style={{ padding: '8px', fontSize: 13, fontFamily: 'sans-serif' }}>
      <div style={{ fontWeight: 600, marginBottom: 8, color: '#374151', borderBottom: '1px solid #e5e7eb', paddingBottom: 4 }}>
        Draft Moves
      </div>

      {/* Children of root */}
      {root.children.map((childId) => {
        const childNode = nodes[childId];
        if (!childNode) return null;
        const isWhite = ((startPly - 1) % 2) === 0;
        const moveNumber = Math.ceil(startPly / 2);
        const prefix = isWhite ? `${moveNumber}. ` : `${moveNumber}... `;
        return (
          <DraftNodeItem
            key={childId}
            nodeId={childId}
            nodes={nodes}
            nodeFen={nodeFen}
            prefix={prefix}
            depth={0}
            onAddMove={addMove}
            onDelete={deleteNode}
            onSetComment={setComment}
          />
        );
      })}

      {/* Input for root (first move) when no children yet */}
      {!hasChildren && (
        <MoveInput
          parentId={rootId}
          parentFen={rootFen}
          onConfirm={addMove}
        />
      )}

      {!hasChildren && (
        <p style={{ marginTop: 8, fontSize: 11, color: '#9ca3af' }}>
          Type a move and press Enter to add it to your draft.
        </p>
      )}
    </div>
  );
}

export default DraftTree;
