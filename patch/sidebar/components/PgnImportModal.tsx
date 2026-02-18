/**
 * PgnImportModal
 *
 * Replaces the window.prompt() PGN import with a proper modal UI.
 *
 * Features:
 * - Textarea for pasting PGN text
 * - File picker for .pgn files
 * - Real-time preview: game count + first-game headers
 * - Error display (non-fatal parse warnings shown as info)
 * - Single-game import: replaces current chapter tree via loadTree()
 * - Multi-game import: confirmation dialog → creates one chapter per game
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';
import { useStudy } from '../../studyContext';
import { importMultiPgn, MultiPgnGame } from '../../pgn/import';
import type { StudyTree as StudyTreeData } from '../../tree/type';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PgnImportModalProps {
  onClose: () => void;
  /** Called after a successful single-game import so callers can react. */
  onSingleImport?: (tree: StudyTreeData) => void;
  /**
   * Called after multi-game chapters have been created.
   * Passes the first new chapter ID so the caller can navigate to it.
   */
  onMultiImport?: (firstChapterId: string) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function gameTitle(headers: Record<string, string>): string {
  const white = headers['White'] ?? '?';
  const black = headers['Black'] ?? '?';
  const event = headers['Event'] ?? '';
  if (white === '?' && black === '?' && !event) return 'Untitled game';
  const players = white === '?' && black === '?' ? '' : `${white} vs ${black}`;
  return [players, event].filter(Boolean).join(' – ');
}

function nodeCount(tree: StudyTreeData): number {
  return Object.keys(tree.nodes).length - 1; // exclude root
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PgnImportModal({ onClose, onSingleImport, onMultiImport }: PgnImportModalProps) {
  const { state, loadTree } = useStudy();
  const { studyId } = state;

  const [pgnText, setPgnText] = useState('');
  const [parsed, setParsed] = useState<ReturnType<typeof importMultiPgn> | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [importErrors, setImportErrors] = useState<string[]>([]);
  const [confirmMulti, setConfirmMulti] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // Re-parse whenever the PGN text changes
  useEffect(() => {
    const text = pgnText.trim();
    if (!text) {
      setParsed(null);
      return;
    }
    const result = importMultiPgn(text, 64);
    setParsed(result);
  }, [pgnText]);

  // File upload handler
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      if (content) setPgnText(content);
    };
    reader.readAsText(file);
    // Reset file input so the same file can be re-selected
    e.target.value = '';
  }, []);

  // Single-game import: replace current chapter tree
  const handleSingleImport = useCallback((game: MultiPgnGame) => {
    loadTree(game.tree);
    onSingleImport?.(game.tree);
    onClose();
  }, [loadTree, onSingleImport, onClose]);

  // Multi-game import: create one chapter per game via API
  const handleMultiImport = useCallback(async () => {
    if (!parsed || !studyId) return;
    setIsImporting(true);
    setImportErrors([]);
    const errs: string[] = [];
    let firstChapterId: string | null = null;

    try {
      for (const game of parsed.games) {
        const title = gameTitle(game.headers) || 'Imported Game';

        let chapterId: string | null = null;

        try {
          if (game.startingFen) {
            // Create chapter from FEN position
            const resp = await api.post('/api/v1/import-export/fen/import', {
              study_id: studyId,
              chapter_title: title,
              fen: game.startingFen,
            });
            chapterId = resp?.chapter?.id ?? resp?.id ?? null;
          } else {
            // Create standard chapter
            const resp = await api.post(
              `/api/v1/workspace/studies/${studyId}/chapters`,
              { title }
            );
            chapterId = resp?.id ?? null;
          }
        } catch (e) {
          errs.push(`Failed to create chapter "${title}": ${e instanceof Error ? e.message : 'error'}`);
          continue;
        }

        if (!chapterId) {
          errs.push(`Could not get chapter ID for "${title}"`);
          continue;
        }

        if (!firstChapterId) firstChapterId = chapterId;

        // Save the tree to the new chapter
        try {
          await api.put(
            `/api/v1/workspace/studies/study-patch/chapter/${chapterId}/tree`,
            game.tree
          );
        } catch (e) {
          errs.push(`Failed to save tree for "${title}": ${e instanceof Error ? e.message : 'error'}`);
        }
      }
    } finally {
      setIsImporting(false);
    }

    if (errs.length > 0) {
      setImportErrors(errs);
    }

    if (firstChapterId) {
      onMultiImport?.(firstChapterId);
      onClose();
    }
  }, [parsed, studyId, onMultiImport, onClose]);

  // Decide what "Import" does
  const handleImportClick = useCallback(() => {
    if (!parsed || parsed.games.length === 0) return;
    if (parsed.games.length === 1) {
      handleSingleImport(parsed.games[0]);
    } else {
      setConfirmMulti(true);
    }
  }, [parsed, handleSingleImport]);

  // ---------------------------------------------------------------------------
  // Preview data
  // ---------------------------------------------------------------------------
  const firstGame = parsed?.games[0];
  const gameCount = parsed?.games.length ?? 0;
  const parseWarnings = firstGame?.errors ?? [];

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Import PGN"
      style={overlayStyle}
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={modalStyle}>
        {/* Header */}
        <div style={headerStyle}>
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>Import PGN</span>
          <button type="button" onClick={onClose} style={closeBtnStyle} aria-label="Close">✕</button>
        </div>

        {/* Textarea */}
        <textarea
          style={textareaStyle}
          placeholder="Paste PGN here…"
          value={pgnText}
          onChange={(e) => setPgnText(e.target.value)}
          spellCheck={false}
        />

        {/* File upload */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
          <button
            type="button"
            style={secondaryBtnStyle}
            onClick={() => fileRef.current?.click()}
          >
            Load .pgn file
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".pgn,text/plain"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          {pgnText && (
            <button
              type="button"
              style={{ ...secondaryBtnStyle, color: '#888' }}
              onClick={() => setPgnText('')}
            >
              Clear
            </button>
          )}
        </div>

        {/* Preview */}
        {parsed && gameCount > 0 && (
          <div style={previewStyle}>
            <div style={{ fontWeight: 600, marginBottom: '6px' }}>
              {gameCount === 1
                ? '1 game found'
                : `${gameCount} games found${parsed.truncated ? ' (truncated to 64)' : ''}`}
            </div>
            {firstGame && (
              <div style={{ fontSize: '12px', color: '#555', lineHeight: 1.5 }}>
                <div><b>First game:</b> {gameTitle(firstGame.headers)}</div>
                {firstGame.startingFen && (
                  <div style={{ color: '#888' }}>
                    Custom starting position (FEN)
                  </div>
                )}
                <div>Moves: {nodeCount(firstGame.tree)}</div>
                {firstGame.errors.length > 0 && (
                  <div style={{ color: '#b45309', marginTop: '4px' }}>
                    ⚠ {firstGame.errors.length} parse warning(s)
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {parsed && gameCount === 0 && (
          <div style={{ color: '#dc2626', fontSize: '12px', marginBottom: '8px' }}>
            No valid PGN games found.
          </div>
        )}

        {/* Non-fatal parse warnings */}
        {parseWarnings.length > 0 && (
          <details style={{ marginBottom: '8px', fontSize: '11px', color: '#92400e' }}>
            <summary style={{ cursor: 'pointer' }}>
              Show {parseWarnings.length} parse warning(s)
            </summary>
            <ul style={{ margin: '4px 0 0 16px', padding: 0 }}>
              {parseWarnings.slice(0, 10).map((w, i) => <li key={i}>{w}</li>)}
              {parseWarnings.length > 10 && <li>…and {parseWarnings.length - 10} more</li>}
            </ul>
          </details>
        )}

        {/* Import errors (from API calls) */}
        {importErrors.length > 0 && (
          <div style={{ color: '#dc2626', fontSize: '12px', marginBottom: '8px' }}>
            {importErrors.map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
          <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
          <button
            type="button"
            onClick={handleImportClick}
            disabled={!parsed || gameCount === 0 || isImporting}
            style={{
              ...primaryBtnStyle,
              opacity: (!parsed || gameCount === 0 || isImporting) ? 0.5 : 1,
              cursor: (!parsed || gameCount === 0 || isImporting) ? 'not-allowed' : 'pointer',
            }}
          >
            {isImporting
              ? 'Importing…'
              : gameCount === 1
                ? 'Import Game'
                : `Import ${gameCount} Games`}
          </button>
        </div>

        {/* Multi-game confirmation */}
        {confirmMulti && parsed && (
          <div style={confirmOverlayStyle}>
            <div style={confirmCardStyle}>
              <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                Create {parsed.games.length} new chapters?
              </div>
              <div style={{ fontSize: '13px', color: '#555', marginBottom: '12px' }}>
                Each game will be imported as a separate chapter in the current study.
                {parsed.truncated && ` (Truncated to ${parsed.games.length} games)`}
              </div>
              <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button
                  type="button"
                  style={secondaryBtnStyle}
                  onClick={() => setConfirmMulti(false)}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  style={primaryBtnStyle}
                  onClick={() => {
                    setConfirmMulti(false);
                    handleMultiImport();
                  }}
                >
                  Create Chapters
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Inline styles
// ---------------------------------------------------------------------------

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0,0,0,0.45)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalStyle: React.CSSProperties = {
  backgroundColor: '#fff',
  borderRadius: '8px',
  padding: '20px',
  width: '480px',
  maxWidth: '95vw',
  maxHeight: '90vh',
  overflowY: 'auto',
  boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  position: 'relative',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '12px',
};

const closeBtnStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  fontSize: '18px',
  cursor: 'pointer',
  color: '#666',
  padding: '0 4px',
};

const textareaStyle: React.CSSProperties = {
  width: '100%',
  height: '160px',
  fontFamily: 'monospace',
  fontSize: '11px',
  border: '1px solid #d1d5db',
  borderRadius: '4px',
  padding: '8px',
  resize: 'vertical',
  marginBottom: '10px',
  boxSizing: 'border-box',
};

const previewStyle: React.CSSProperties = {
  backgroundColor: '#f3f4f6',
  borderRadius: '6px',
  padding: '10px 12px',
  marginBottom: '10px',
  fontSize: '13px',
};

const primaryBtnStyle: React.CSSProperties = {
  padding: '7px 16px',
  backgroundColor: '#3b82f6',
  color: '#fff',
  border: 'none',
  borderRadius: '5px',
  cursor: 'pointer',
  fontSize: '13px',
  fontWeight: 600,
};

const secondaryBtnStyle: React.CSSProperties = {
  padding: '7px 14px',
  backgroundColor: '#f3f4f6',
  color: '#374151',
  border: '1px solid #d1d5db',
  borderRadius: '5px',
  cursor: 'pointer',
  fontSize: '13px',
};

const confirmOverlayStyle: React.CSSProperties = {
  position: 'absolute',
  inset: 0,
  backgroundColor: 'rgba(255,255,255,0.9)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '8px',
  zIndex: 10,
};

const confirmCardStyle: React.CSSProperties = {
  backgroundColor: '#fff',
  border: '1px solid #e5e7eb',
  borderRadius: '8px',
  padding: '20px',
  width: '340px',
  boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
};
