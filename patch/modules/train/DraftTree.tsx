/**
 * DraftTree.tsx - Draft move tree for train mode.
 *
 * Layout mirrors study movetree.tsx:
 *   - White/black paired grid (2-column)
 *   - Variation indentation with collapse/expand
 *
 * Key differences from movetree:
 *   - Uses DraftNode (local state), no useStudy() context
 *   - No cursor navigation
 *   - '+' on non-leaf nodes opens a MoveInput for adding a variation
 *   - Always-visible MoveInput at each branch leaf for extending the line
 *   - '×' delete button on every node
 *   - Root-level '+' button for adding alternative first moves
 */

import React, { useState, useCallback } from 'react';
import type { DraftNode, UseDraftTreeReturn, AddMoveResult } from './useDraftTree';
import { validateMove } from '../../chessJS/replay';
import { getStartPlyFromFen } from './trainUtils';

// ─── MoveInput ────────────────────────────────────────────────────────────────

interface MoveInputProps {
  parentId: string;
  parentFen: string;
  onConfirm: (parentId: string, san: string) => AddMoveResult;
  onCancel?: () => void;
  autoFocus?: boolean;
}

function MoveInput({ parentId, parentFen, onConfirm, onCancel, autoFocus = false }: MoveInputProps) {
  const [value, setValue] = useState('');
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const validate = (san: string) => {
    if (!san.trim()) { setIsValid(null); setErrorMsg(null); return; }
    const result = validateMove(parentFen, san.trim());
    setIsValid(result.valid);
    setErrorMsg(result.valid ? null : (result.error || 'Invalid move'));
  };

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
      onCancel?.();
    }
  };

  const borderColor = isValid === true ? '#16a34a' : isValid === false ? '#dc2626' : '#d1d5db';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
      <input
        // eslint-disable-next-line jsx-a11y/no-autofocus
        autoFocus={autoFocus}
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
        <span
          style={{ fontSize: 11, color: '#dc2626', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
          title={errorMsg}
        >
          {errorMsg}
        </span>
      )}
    </div>
  );
}

// ─── DraftMoveItem ────────────────────────────────────────────────────────────

interface DraftMoveItemProps {
  nodeId: string;
  nodes: Record<string, DraftNode>;
  isMainline: boolean;
  prefix?: string;
  onDelete: (nodeId: string) => void;
  onSetComment: (nodeId: string, comment: string) => void;
  /** Called when user clicks '+'; pass nodeId to open variation input for this node */
  onAddVariation: (nodeId: string) => void;
}

function DraftMoveItem({
  nodeId,
  nodes,
  isMainline,
  prefix = '',
  onDelete,
  onSetComment,
  onAddVariation,
}: DraftMoveItemProps) {
  const node = nodes[nodeId];
  const [showComment, setShowComment] = useState(false);
  if (!node) return null;

  const isLeaf = node.children.length === 0;

  return (
    <div className="move-item" style={{ margin: '1px 0' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          padding: '1px 2px',
          borderRadius: 3,
          whiteSpace: 'nowrap',
        }}
      >
        {/* Move text */}
        <span
          style={{
            padding: '2px 5px',
            borderRadius: 3,
            fontWeight: isMainline ? 'bold' : 'normal',
            color: isMainline ? '#000' : '#444',
            userSelect: 'none',
          }}
        >
          {prefix && <span style={{ marginRight: 3 }}>{prefix}</span>}
          <span>{node.san}</span>
        </span>

        {/* Comment toggle button */}
        <button
          type="button"
          onClick={() => setShowComment((v) => !v)}
          title={showComment ? 'Hide comment' : 'Add/edit comment'}
          style={{
            padding: '0 4px',
            fontSize: 11,
            lineHeight: '16px',
            border: '1px solid #d1d5db',
            borderRadius: 3,
            background: showComment ? '#fef9c3' : '#f9fafb',
            color: '#6b7280',
            cursor: 'pointer',
          }}
        >
          {node.comment ? '💬' : '+'}
        </button>

        {/* + button: add variation from this node's resulting position (non-leaf only) */}
        {!isLeaf && (
          <button
            type="button"
            title="Add variation from this position"
            onClick={() => onAddVariation(nodeId)}
            style={{
              padding: '0 4px',
              fontSize: 11,
              lineHeight: '16px',
              border: '1px solid #d1d5db',
              borderRadius: 3,
              background: '#f9fafb',
              color: '#6b7280',
              cursor: 'pointer',
            }}
          >
            ⑂
          </button>
        )}

        {/* × delete button */}
        <button
          type="button"
          title="Delete this move and all following moves in this branch"
          onClick={() => onDelete(nodeId)}
          style={{
            padding: '0 4px',
            fontSize: 11,
            lineHeight: '16px',
            border: '1px solid #fca5a5',
            borderRadius: 3,
            background: '#fef2f2',
            color: '#dc2626',
            cursor: 'pointer',
          }}
        >
          ×
        </button>
      </div>

      {/* Inline comment textarea */}
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
            display: 'block',
          }}
        />
      )}
    </div>
  );
}

// ─── DraftMoveBranch ─────────────────────────────────────────────────────────

interface DraftMoveBranchProps {
  startNodeId: string;
  nodes: Record<string, DraftNode>;
  nodeFen: Map<string, string>;
  depth: number;
  startPly: number;
  isMainline: boolean;
  collapsedVariations: Set<string>;
  activeInputId: string | null;
  onToggleVariation: (nodeId: string) => void;
  onAddMove: (parentId: string, san: string) => AddMoveResult;
  onDelete: (nodeId: string) => void;
  onSetComment: (nodeId: string, comment: string) => void;
  onSetActiveInput: (nodeId: string | null) => void;
}

function DraftMoveBranch({
  startNodeId,
  nodes,
  nodeFen,
  depth,
  startPly,
  isMainline,
  collapsedVariations,
  activeInputId,
  onToggleVariation,
  onAddMove,
  onDelete,
  onSetComment,
  onSetActiveInput,
}: DraftMoveBranchProps) {
  if (!startNodeId || !nodes[startNodeId]) return null;

  /**
   * Renders existing variation children of nodeId (children[1..n]) plus,
   * if activeInputId === nodeId, a MoveInput for adding a new variation.
   */
  const renderVariationsWithInput = (nodeId: string, ply: number) => {
    const node = nodes[nodeId];
    const variationIds = node?.children.slice(1) ?? [];
    const hasActiveInput = activeInputId === nodeId;
    const parentFen = nodeFen.get(nodeId);

    if (variationIds.length === 0 && !hasActiveInput) return null;

    return (
      <div
        key={`vars-${nodeId}`}
        className="variations"
        style={{
          fontSize: '12.6px',
          color: '#555',
          marginTop: '4px',
          marginBottom: '4px',
          borderLeft: '2px solid #ddd',
          paddingLeft: '8px',
          marginLeft: '12px',
        }}
      >
        {variationIds.map((vId) => (
          <div key={vId} className="variation-wrapper" style={{ marginBottom: '4px' }}>
            <button
              type="button"
              onClick={() => onToggleVariation(vId)}
              style={{
                marginRight: '6px',
                padding: '0 6px',
                border: '1px solid #ccc',
                background: '#fff',
                cursor: 'pointer',
              }}
            >
              {collapsedVariations.has(vId) ? '+' : '-'}
            </button>
            <span style={{ color: '#888', marginRight: '4px' }}>(variation)</span>
            {!collapsedVariations.has(vId) && (
              <DraftMoveBranch
                startNodeId={vId}
                nodes={nodes}
                nodeFen={nodeFen}
                depth={depth + 1}
                startPly={ply}
                isMainline={false}
                collapsedVariations={collapsedVariations}
                activeInputId={activeInputId}
                onToggleVariation={onToggleVariation}
                onAddMove={onAddMove}
                onDelete={onDelete}
                onSetComment={onSetComment}
                onSetActiveInput={onSetActiveInput}
              />
            )}
          </div>
        ))}

        {hasActiveInput && parentFen && (
          <div style={{ marginTop: 4 }}>
            <MoveInput
              parentId={nodeId}
              parentFen={parentFen}
              autoFocus
              onConfirm={(pid, san) => {
                const result = onAddMove(pid, san);
                if (result.ok) onSetActiveInput(null);
                return result;
              }}
              onCancel={() => onSetActiveInput(null)}
            />
          </div>
        )}
      </div>
    );
  };

  const lines: React.ReactNode[] = [];
  const lineStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'max-content max-content',
    gap: '6px',
    marginBottom: '4px',
    alignItems: 'center',
  };

  let currentId: string | null = startNodeId;
  let ply = startPly;
  let lastId: string | null = null;

  while (currentId) {
    const currentNode = nodes[currentId];
    if (!currentNode) break;

    lastId = currentId;
    const isWhite = ply % 2 === 1;
    const moveNumber = Math.floor((ply + 1) / 2);

    if (isWhite) {
      const whiteNode = currentNode;
      const blackId = whiteNode.children[0] || null;
      const blackNode = blackId ? nodes[blackId] : null;

      // Split the pair into individual rows when either node has sibling
      // variations (or an active input), so each variation/input block
      // appears directly below its branching move.
      const shouldSplitPair = (
        whiteNode.children.length > 1 ||
        (blackNode !== null && blackNode.children.length > 1) ||
        activeInputId === whiteNode.id ||
        (blackNode !== null && activeInputId === blackNode.id)
      );

      if (shouldSplitPair) {
        // White alone
        lines.push(
          <div key={`line-white-${currentId}`} className="move-line" style={lineStyle}>
            <DraftMoveItem nodeId={whiteNode.id} nodes={nodes} isMainline={isMainline} prefix={`${moveNumber}.`} onDelete={onDelete} onSetComment={onSetComment} onAddVariation={onSetActiveInput} />
            <div />
          </div>
        );
        lines.push(renderVariationsWithInput(whiteNode.id, ply + 1));
        if (blackNode) {
          // Black alone
          lines.push(
            <div key={`line-black-${blackNode.id}`} className="move-line" style={lineStyle}>
              <div />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <DraftMoveItem nodeId={blackNode.id} nodes={nodes} isMainline={isMainline} prefix={`${moveNumber}...`} onDelete={onDelete} onSetComment={onSetComment} onAddVariation={onSetActiveInput} />
              </div>
            </div>
          );
          lines.push(renderVariationsWithInput(blackNode.id, ply + 2));
          lastId = blackNode.id;
          currentId = blackNode.children[0] || null;
          ply += 2;
        } else {
          currentId = null;
        }
      } else if (blackNode) {
        // Normal pair (no variations, no active input)
        lines.push(
          <div key={`line-pair-${currentId}`} className="move-line" style={lineStyle}>
            <DraftMoveItem nodeId={whiteNode.id} nodes={nodes} isMainline={isMainline} prefix={`${moveNumber}.`} onDelete={onDelete} onSetComment={onSetComment} onAddVariation={onSetActiveInput} />
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <DraftMoveItem nodeId={blackNode.id} nodes={nodes} isMainline={isMainline} prefix={`${moveNumber}...`} onDelete={onDelete} onSetComment={onSetComment} onAddVariation={onSetActiveInput} />
            </div>
          </div>
        );
        lastId = blackNode.id;
        currentId = blackNode.children[0] || null;
        ply += 2;
      } else {
        // White is leaf of mainline
        lines.push(
          <div key={`line-white-${currentId}`} className="move-line" style={lineStyle}>
            <DraftMoveItem nodeId={whiteNode.id} nodes={nodes} isMainline={isMainline} prefix={`${moveNumber}.`} onDelete={onDelete} onSetComment={onSetComment} onAddVariation={onSetActiveInput} />
            <div />
          </div>
        );
        lines.push(renderVariationsWithInput(whiteNode.id, ply + 1));
        currentId = null;
      }
    } else {
      // Starts with black (odd startPly)
      const blackNode = currentNode;
      lines.push(
        <div key={`line-black-${currentId}`} className="move-line" style={lineStyle}>
          <div />
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <DraftMoveItem
              nodeId={blackNode.id}
              nodes={nodes}
              isMainline={isMainline}
              prefix={`${moveNumber}...`}
              onDelete={onDelete}
              onSetComment={onSetComment}
              onAddVariation={onSetActiveInput}
            />
          </div>
        </div>
      );
      lines.push(renderVariationsWithInput(blackNode.id, ply + 1));
      currentId = blackNode.children[0] || null;
      ply += 1;
    }
  }

  // Always-visible MoveInput at the leaf of this branch
  if (lastId) {
    const lastNode = nodes[lastId];
    const isLeaf = lastNode && lastNode.children.length === 0;
    const leafFen = nodeFen.get(lastId);
    if (isLeaf && leafFen) {
      lines.push(
        <div key={`leaf-input-${lastId}`} style={{ marginTop: 4 }}>
          <MoveInput
            parentId={lastId}
            parentFen={leafFen}
            onConfirm={onAddMove}
          />
        </div>
      );
    }
  }

  return (
    <div className="move-branch" style={{ marginLeft: depth > 0 ? '12px' : '0' }}>
      {lines}
    </div>
  );
}

// ─── DraftTree ────────────────────────────────────────────────────────────────

export interface DraftTreeProps {
  draft: UseDraftTreeReturn;
}

export function DraftTree({ draft }: DraftTreeProps) {
  const [collapsedVariations, setCollapsedVariations] = useState<Set<string>>(new Set());
  const [activeInputId, setActiveInputId] = useState<string | null>(null);

  const { nodes, nodeFen, rootId, startFen, addMove, deleteNode, setComment } = draft;
  const root = nodes[rootId];
  const rootFen = nodeFen.get(rootId) ?? startFen;
  const startPly = getStartPlyFromFen(startFen);

  const toggleVariation = useCallback((nodeId: string) => {
    setCollapsedVariations((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) next.delete(nodeId);
      else next.add(nodeId);
      return next;
    });
  }, []);

  if (!root) return null;

  // Empty tree: show initial MoveInput
  if (root.children.length === 0) {
    return (
      <div style={{ padding: '8px', fontSize: 14, fontFamily: 'sans-serif' }}>
        <MoveInput parentId={rootId} parentFen={rootFen} onConfirm={addMove} />
        <p style={{ marginTop: 8, fontSize: 11, color: '#9ca3af' }}>
          Type a move and press Enter to start your draft.
        </p>
      </div>
    );
  }

  const hasRootAlternatives = root.children.length > 1;

  return (
    <div style={{ padding: '8px', fontSize: 14, fontFamily: 'sans-serif', overflowY: 'auto' }}>

      {/* Header with '+' button for alternative first moves */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        marginBottom: 6,
        paddingBottom: 4,
        borderBottom: '1px solid #e5e7eb',
      }}>
        <span style={{ fontWeight: 600, color: '#374151', fontSize: 13 }}>Draft Moves</span>
        <button
          type="button"
          title="Add alternative first move"
          onClick={() => setActiveInputId((prev) => prev === rootId ? null : rootId)}
          style={{
            padding: '0 5px',
            fontSize: 11,
            lineHeight: '16px',
            border: '1px solid #d1d5db',
            borderRadius: 3,
            background: activeInputId === rootId ? '#dbeafe' : '#f9fafb',
            color: '#6b7280',
            cursor: 'pointer',
          }}
        >
          +
        </button>
      </div>

      {/* Root-level alternative first moves */}
      {(hasRootAlternatives || activeInputId === rootId) && (
        <div style={{
          fontSize: '12.6px',
          color: '#555',
          marginBottom: '8px',
          borderLeft: '2px solid #ddd',
          paddingLeft: '8px',
          marginLeft: '12px',
        }}>
          {root.children.slice(1).map((vId) => (
            <div key={vId} style={{ marginBottom: 4 }}>
              <button
                type="button"
                onClick={() => toggleVariation(vId)}
                style={{
                  marginRight: '6px',
                  padding: '0 6px',
                  border: '1px solid #ccc',
                  background: '#fff',
                  cursor: 'pointer',
                }}
              >
                {collapsedVariations.has(vId) ? '+' : '-'}
              </button>
              <span style={{ color: '#888', marginRight: 4 }}>(variation)</span>
              {!collapsedVariations.has(vId) && (
                <DraftMoveBranch
                  startNodeId={vId}
                  nodes={nodes}
                  nodeFen={nodeFen}
                  depth={1}
                  startPly={startPly}
                  isMainline={false}
                  collapsedVariations={collapsedVariations}
                  activeInputId={activeInputId}
                  onToggleVariation={toggleVariation}
                  onAddMove={addMove}
                  onDelete={deleteNode}
                  onSetComment={setComment}
                  onSetActiveInput={setActiveInputId}
                />
              )}
            </div>
          ))}

          {activeInputId === rootId && (
            <div style={{ marginTop: 4 }}>
              <MoveInput
                parentId={rootId}
                parentFen={rootFen}
                autoFocus
                onConfirm={(pid, san) => {
                  const result = addMove(pid, san);
                  if (result.ok) setActiveInputId(null);
                  return result;
                }}
                onCancel={() => setActiveInputId(null)}
              />
            </div>
          )}
        </div>
      )}

      {/* Main line */}
      <DraftMoveBranch
        startNodeId={root.children[0]}
        nodes={nodes}
        nodeFen={nodeFen}
        depth={0}
        startPly={startPly}
        isMainline={true}
        collapsedVariations={collapsedVariations}
        activeInputId={activeInputId}
        onToggleVariation={toggleVariation}
        onAddMove={addMove}
        onDelete={deleteNode}
        onSetComment={setComment}
        onSetActiveInput={setActiveInputId}
      />
    </div>
  );
}

export default DraftTree;
