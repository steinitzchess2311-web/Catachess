import React from 'react';
import { useStudy } from '../studyContext';
import { importPgn } from '../pgn/import';
import { StudyNode } from '../tree/type';

export interface MoveTreeProps {
  className?: string;
}

/**
 * MoveTree - Displays the chess move tree in the sidebar
 * Supports recursive rendering of mainline and variations.
 */
export function MoveTree({ className }: MoveTreeProps) {
  const {
    state,
    selectNode,
    selectChapter,
    loadTreeFromServer,
    loadTree,
    setError,
    clearError,
    saveTree,
    deleteMove,
    promoteVariation,
  } = useStudy();
  const [collapsedVariations, setCollapsedVariations] = React.useState<Set<string>>(new Set());
  const [menuState, setMenuState] = React.useState<{
    nodeId: string;
    x: number;
    y: number;
    canPromote: boolean;
  } | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = React.useState<string | null>(null);
  const { tree, cursorNodeId } = state;

  const handleReload = () => {
    if (state.chapterId) {
      selectChapter(state.chapterId);
      return;
    }
    loadTreeFromServer();
  };

  if (!tree || !tree.nodes || !tree.rootId || !cursorNodeId) {
    return (
      <div className={`move-tree-container ${className || ''}`} style={{ padding: '20px', color: '#666', fontStyle: 'italic' }}>
        <div style={{ marginBottom: '8px' }}>Move tree unavailable.</div>
        <button
          type="button"
          onClick={handleReload}
          style={{
            padding: '6px 10px',
            backgroundColor: '#4a4a4a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reload Chapter
        </button>
      </div>
    );
  }

  const rootNode = tree.nodes[tree.rootId];
  if (!rootNode || !tree.nodes[cursorNodeId]) {
    return (
      <div className={`move-tree-container ${className || ''}`} style={{ padding: '20px', color: '#666', fontStyle: 'italic' }}>
        <div style={{ marginBottom: '8px' }}>Move tree unavailable.</div>
        <button
          type="button"
          onClick={handleReload}
          style={{
            padding: '6px 10px',
            backgroundColor: '#4a4a4a',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reload Chapter
        </button>
      </div>
    );
  }

  const handleNodeClick = (nodeId: string) => {
    selectNode(nodeId);
  };

  const handleContainerContextMenu = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
  };

  const handleContextMenu = (nodeId: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    const node = tree.nodes[nodeId];
    const parentId = node?.parentId;
    const canPromote = Boolean(
      parentId && tree.nodes[parentId]?.children?.[0] && tree.nodes[parentId]?.children[0] !== nodeId
    );
    setMenuState({
      nodeId,
      x: event.clientX,
      y: event.clientY,
      canPromote,
    });
  };

  React.useEffect(() => {
    // Close handled by onMouseLeave of the menu to keep behavior consistent with hover.
    if (!menuState) return;
  }, [menuState]);

  const toggleVariation = (nodeId: string) => {
    setCollapsedVariations((prev) => {
      const next = new Set(prev);
      if (next.has(nodeId)) {
        next.delete(nodeId);
      } else {
        next.add(nodeId);
      }
      return next;
    });
  };

  const handleImportClick = () => {
    const pgnContent = window.prompt('Paste PGN to import');
    if (!pgnContent) return;

    clearError();
    const result = importPgn(pgnContent);
    if (!result.success || !result.tree) {
      const message = result.errors.length > 0 ? result.errors.join('; ') : 'Failed to import PGN';
      setError('LOAD_ERROR', message, { errors: result.errors });
      return;
    }

    loadTree(result.tree);
  };

  return (
    <div
      className={`move-tree-container ${className || ''}`}
      onContextMenu={handleContainerContextMenu}
      style={{ 
        padding: '10px', 
        fontFamily: 'sans-serif',
        fontSize: '14px',
        overflowY: 'auto'
      }}
    >
      <div className="move-tree-title" style={{ fontWeight: 'bold', marginBottom: '10px', borderBottom: '1px solid #ddd', paddingBottom: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Move Tree</span>
        <div className="tree-controls" style={{ fontSize: '0.8em' }}>
          <button onClick={handleImportClick} style={{ marginRight: '5px' }}>Import</button>
        </div>
      </div>
      <div className="move-tree-content">
        {rootNode && rootNode.children.length > 0 && (
          <MoveBranch 
            startNodeId={rootNode.children[0]}
            nodes={tree.nodes} 
            cursorNodeId={cursorNodeId} 
            onSelect={handleNodeClick} 
            depth={0}
            startPly={1}
            isMainline={true}
            rootId={tree.rootId}
            collapsedVariations={collapsedVariations}
            onToggleVariation={toggleVariation}
            onContextMenu={handleContextMenu}
          />
        )}
      </div>
      {menuState && (
        <div
          className="patch-context-menu"
          style={{ top: menuState.y, left: menuState.x }}
          onMouseLeave={() => setMenuState(null)}
        >
          <button
            type="button"
            className="patch-context-item"
            disabled={!menuState.canPromote}
            onClick={() => {
              promoteVariation(menuState.nodeId);
              setMenuState(null);
            }}
          >
            Promote to Mainline
          </button>
          <button
            type="button"
            className="patch-context-item is-danger"
            onClick={() => {
              setConfirmDeleteId(menuState.nodeId);
              setMenuState(null);
            }}
          >
            Delete Branch
          </button>
        </div>
      )}
      {confirmDeleteId && (
        <div className="patch-confirm-overlay">
          <div className="patch-confirm-card">
            <div className="patch-confirm-title">Delete branch?</div>
            <div className="patch-confirm-body">
              This will delete this move and all following moves in this branch.
            </div>
            <div className="patch-confirm-actions">
              <button
                type="button"
                className="patch-confirm-btn"
                onClick={() => setConfirmDeleteId(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="patch-confirm-btn is-danger"
                onClick={() => {
                  deleteMove(confirmDeleteId);
                  setConfirmDeleteId(null);
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

interface MoveBranchProps {
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  onSelect: (nodeId: string) => void;
  depth: number;
  startNodeId: string;
  startPly: number;
  isMainline: boolean;
  rootId?: string;
  collapsedVariations: Set<string>;
  onToggleVariation: (nodeId: string) => void;
  onContextMenu: (nodeId: string, event: React.MouseEvent) => void;
}

/**
 * Renders a branch of moves (mainline + variations)
 */
function MoveBranch({
  startNodeId,
  nodes,
  cursorNodeId,
  onSelect,
  depth,
  startPly,
  isMainline,
  rootId,
  collapsedVariations,
  onToggleVariation,
  onContextMenu,
}: MoveBranchProps) {
  if (!startNodeId) return null;

  const renderVariations = (nodeId: string, ply: number, overrideIds?: string[]) => {
    const node = nodes[nodeId];
    const variationsIds = overrideIds || node?.children.slice(1) || [];
    if (!node || variationsIds.length === 0) return null;
    return (
      <div className="variations" style={{ 
        fontSize: '12.6px', 
        color: '#555', 
        marginTop: '4px',
        marginBottom: '4px',
        borderLeft: '2px solid #ddd',
        paddingLeft: '8px',
        marginLeft: '12px'
      }}>
        {variationsIds.map((vId) => (
          <div
            key={vId}
            className="variation-wrapper"
            style={{ marginBottom: '4px' }}
            onContextMenu={(event) => onContextMenu(vId, event)}
            onDoubleClick={(event) => onContextMenu(vId, event)}
          >
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
              <MoveBranch
                startNodeId={vId}
                nodes={nodes}
                cursorNodeId={cursorNodeId}
                onSelect={onSelect}
                depth={depth + 1}
                startPly={ply}
                isMainline={false}
                rootId={undefined}
                collapsedVariations={collapsedVariations}
                onToggleVariation={onToggleVariation}
              />
            )}
          </div>
        ))}
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

  while (currentId) {
    const currentNode = nodes[currentId];
    if (!currentNode) break;

    const isWhite = ply % 2 === 1;
    const moveNumber = Math.floor((ply + 1) / 2);
    if (isWhite) {
      const whiteNode = currentNode;
      const blackId = whiteNode.children[0] || null;
      const blackNode = blackId ? nodes[blackId] : null;
      const rootNode = rootId ? nodes[rootId] : null;
      const hasRootVariations =
        isMainline &&
        depth === 0 &&
        rootId &&
        currentId === startNodeId &&
        ply === startPly &&
        (rootNode?.children.length || 0) > 1;

      if (hasRootVariations) {
        lines.push(
          <div key={`line-white-${currentId}`} className="move-line" style={lineStyle}>
            <MoveItem
              nodeId={whiteNode.id}
              nodes={nodes}
              cursorNodeId={cursorNodeId}
              onSelect={onSelect}
              isMainline={isMainline}
              prefix={`${moveNumber}.`}
              onContextMenu={onContextMenu}
            />
            <div />
          </div>
        );
        lines.push(renderVariations(rootId!, 1, rootNode!.children.slice(1)));
      } else if (blackNode) {
        lines.push(
          <div key={`line-pair-${currentId}`} className="move-line" style={lineStyle}>
            <MoveItem
              nodeId={whiteNode.id}
              nodes={nodes}
              cursorNodeId={cursorNodeId}
              onSelect={onSelect}
              isMainline={isMainline}
              prefix={`${moveNumber}.`}
              onContextMenu={onContextMenu}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <MoveItem
                nodeId={blackNode.id}
                nodes={nodes}
                cursorNodeId={cursorNodeId}
                onSelect={onSelect}
                isMainline={isMainline}
                prefix={`${moveNumber}...`}
                onContextMenu={onContextMenu}
              />
            </div>
          </div>
        );
      } else {
        lines.push(
          <div key={`line-white-${currentId}`} className="move-line" style={lineStyle}>
            <MoveItem
              nodeId={whiteNode.id}
              nodes={nodes}
              cursorNodeId={cursorNodeId}
              onSelect={onSelect}
              isMainline={isMainline}
              prefix={`${moveNumber}.`}
              onContextMenu={onContextMenu}
            />
            <div />
          </div>
        );
      }

      if (blackNode) {
        if (hasRootVariations) {
          lines.push(
            <div key={`line-black-${blackNode.id}`} className="move-line" style={lineStyle}>
            <div />
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <MoveItem
                nodeId={blackNode.id}
                nodes={nodes}
                cursorNodeId={cursorNodeId}
                onSelect={onSelect}
                isMainline={isMainline}
                prefix={`${moveNumber}...`}
                onContextMenu={onContextMenu}
              />
            </div>
          </div>
        );
        }

        lines.push(renderVariations(whiteNode.id, ply + 1));
        lines.push(renderVariations(blackNode.id, ply + 2));

        currentId = blackNode.children[0] || null;
        ply += 2;
      } else {
        currentId = null;
      }
    } else {
      const blackNode = currentNode;
      lines.push(
      <div key={`line-black-${currentId}`} className="move-line" style={lineStyle}>
          <div />
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <MoveItem
              nodeId={blackNode.id}
              nodes={nodes}
              cursorNodeId={cursorNodeId}
              onSelect={onSelect}
              isMainline={isMainline}
              prefix={`${moveNumber}...`}
              onContextMenu={onContextMenu}
            />
          </div>
        </div>
      );
      lines.push(renderVariations(blackNode.id, ply + 1));
      currentId = blackNode.children[0] || null;
      ply += 1;
    }
  }

  return (
    <div className="move-branch" style={{ marginLeft: depth > 0 ? '12px' : '0' }}>
      {lines}
    </div>
  );
}

interface MoveItemProps {
  nodeId: string;
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  onSelect: (nodeId: string) => void;
  isMainline: boolean;
  prefix?: string;
  onContextMenu: (nodeId: string, event: React.MouseEvent) => void;
}

function MoveItem({
  nodeId,
  nodes,
  cursorNodeId,
  onSelect,
  isMainline,
  prefix = '',
  onContextMenu,
}: MoveItemProps) {
  const node = nodes[nodeId];
  if (!node) return null;

  const isActive = cursorNodeId === nodeId;

  return (
    <div 
      className={`move-item ${isActive ? 'active' : ''}`}
      onClick={(e) => {
        e.stopPropagation();
        onSelect(nodeId);
      }}
      onDoubleClick={(e) => {
        e.stopPropagation();
        onContextMenu(nodeId, e);
      }}
      onContextMenu={(e) => onContextMenu(nodeId, e)}
      style={{
        display: 'block',
        width: 'max-content',
        textAlign: 'left',
        padding: '2px 6px',
        margin: '2px',
        borderRadius: '3px',
        cursor: 'pointer',
        backgroundColor: isActive ? '#3b82f6' : 'transparent',
        color: isActive ? 'white' : (isMainline ? '#000' : '#444'),
        fontWeight: isMainline ? 'bold' : 'normal',
        border: isActive ? 'none' : '1px solid transparent',
        transition: 'all 0.1s',
        whiteSpace: 'nowrap',
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = '#e5e7eb';
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      {prefix && <span className="move-prefix" style={{ marginRight: '4px' }}>{prefix}</span>}
      <span className="move-san">{node.san}</span>
      {node.nags && node.nags.length > 0 && (
        <span className="move-nags" style={{ marginLeft: '2px', color: isActive ? 'white' : '#d97706' }}>
          {node.nags.map(nagToSymbol).join('')}
        </span>
      )}
      {node.comment && (
        <span className="move-comment-icon" title={node.comment} style={{ marginLeft: '4px', opacity: 0.6 }}>
          💬
        </span>
      )}
    </div>
  );
}

/**
 * Simple NAG to Symbol mapping
 */
function nagToSymbol(nag: number): string {
  const map: Record<number, string> = {
    1: '!',
    2: '?',
    3: '!!',
    4: '??',
    5: '!?',
    6: '?!',
  };
  return map[nag] || '';
}

export default MoveTree;
