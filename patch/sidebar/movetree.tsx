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
  const { state, selectNode, selectChapter, loadTreeFromServer, loadTree, setError, clearError } = useStudy();
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

  if (!rootNode || rootNode.children.length === 0) {
    return (
      <div className={`move-tree-container ${className || ''}`} style={{ padding: '20px', color: '#666', fontStyle: 'italic' }}>
        No moves yet. Start playing on the board!
      </div>
    );
  }

  return (
    <div className={`move-tree-container ${className || ''}`} style={{ 
      padding: '10px', 
      fontFamily: 'sans-serif',
      fontSize: '14px',
      backgroundColor: '#f5f5f5',
      height: '100%',
      overflowY: 'auto'
    }}>
      <div className="move-tree-title" style={{ fontWeight: 'bold', marginBottom: '10px', borderBottom: '1px solid #ddd', paddingBottom: '5px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>Move Tree</span>
        <div className="tree-controls" style={{ fontSize: '0.8em' }}>
          <button onClick={handleImportClick} style={{ marginRight: '5px' }}>Import</button>
          <button onClick={() => console.log('Export PGN clicked')}>Export</button>
        </div>
      </div>
      <div className="move-tree-content">
        <MoveBranch 
          nodeIds={rootNode.children} 
          nodes={tree.nodes} 
          cursorNodeId={cursorNodeId} 
          onSelect={handleNodeClick} 
          depth={0}
        />
      </div>
    </div>
  );
}

interface MoveBranchProps {
  nodeIds: string[];
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  onSelect: (nodeId: string) => void;
  depth: number;
}

/**
 * Renders a branch of moves (mainline + variations)
 */
function MoveBranch({ nodeIds, nodes, cursorNodeId, onSelect, depth }: MoveBranchProps) {
  if (nodeIds.length === 0) return null;

  // children[0] is the mainline
  // children[1..n] are variations
  const mainlineId = nodeIds[0];
  const variationsIds = nodeIds.slice(1);

  return (
    <div className="move-branch" style={{ marginLeft: depth > 0 ? '12px' : '0' }}>
      {/* 1. The mainline node */}
      <MoveItem 
        nodeId={mainlineId} 
        nodes={nodes} 
        cursorNodeId={cursorNodeId} 
        onSelect={onSelect} 
        isMainline={true}
      />

      {/* 2. Variations (if any) starting from this point */}
      {variationsIds.length > 0 && (
        <div className="variations" style={{ 
          fontSize: '0.9em', 
          color: '#555', 
          marginTop: '4px',
          marginBottom: '4px',
          borderLeft: '2px solid #ddd',
          paddingLeft: '8px'
        }}>
          {variationsIds.map((vId) => (
            <div key={vId} className="variation-wrapper" style={{ marginBottom: '2px' }}>
              <span style={{ color: '#888', marginRight: '4px' }}>(variation)</span>
              <MoveItem 
                nodeId={vId} 
                nodes={nodes} 
                cursorNodeId={cursorNodeId} 
                onSelect={onSelect} 
                isMainline={false}
              />
            </div>
          ))}
        </div>
      )}

      {/* 3. Continue the mainline from the mainline node's children */}
      {nodes[mainlineId] && nodes[mainlineId].children.length > 0 && (
        <MoveBranch 
          nodeIds={nodes[mainlineId].children} 
          nodes={nodes} 
          cursorNodeId={cursorNodeId} 
          onSelect={onSelect} 
          depth={depth} // We don't increment depth for mainline continuation to keep it vertically aligned
        />
      )}
    </div>
  );
}

interface MoveItemProps {
  nodeId: string;
  nodes: Record<string, StudyNode>;
  cursorNodeId: string;
  onSelect: (nodeId: string) => void;
  isMainline: boolean;
}

function MoveItem({ nodeId, nodes, cursorNodeId, onSelect, isMainline }: MoveItemProps) {
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
      style={{
        display: 'inline-block',
        padding: '2px 6px',
        margin: '2px',
        borderRadius: '3px',
        cursor: 'pointer',
        backgroundColor: isActive ? '#3b82f6' : 'transparent',
        color: isActive ? 'white' : (isMainline ? '#000' : '#444'),
        fontWeight: isMainline ? 'bold' : 'normal',
        border: isActive ? 'none' : '1px solid transparent',
        transition: 'all 0.1s'
      }}
      onMouseEnter={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = '#e5e7eb';
      }}
      onMouseLeave={(e) => {
        if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
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
