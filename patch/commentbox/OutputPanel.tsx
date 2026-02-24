import React, { useEffect, useState } from 'react';
import { useStudy } from '../studyContext';

interface OutputPanelProps {
  /** Buttons rendered in the action row below the FEN card. */
  exportActions?: React.ReactNode;
}

export function OutputPanel({ exportActions }: OutputPanelProps) {
  const { state } = useStudy();
  const fen = state.currentFen || '';
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');

  useEffect(() => {
    if (copyState === 'idle') return;
    const t = window.setTimeout(() => setCopyState('idle'), 1500);
    return () => window.clearTimeout(t);
  }, [copyState]);

  const handleCopyFen = async () => {
    if (!fen) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(fen);
      } else {
        const el = document.createElement('textarea');
        el.value = fen;
        el.style.position = 'absolute';
        el.style.left = '-9999px';
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
      }
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };

  return (
    <div className="study-info-panel">
      <div className="study-output-card">
        <div className="study-output-card-header">
          <span className="study-output-card-label">Current FEN</span>
          <button
            type="button"
            className="study-fen-button study-output-copy-btn"
            onClick={handleCopyFen}
            disabled={!fen}
          >
            {copyState === 'copied' ? 'Copied' : copyState === 'error' ? 'Copy failed' : 'Copy FEN'}
          </button>
        </div>
        <textarea
          className="study-fen-box study-output-fen-box"
          readOnly
          value={fen || 'FEN unavailable'}
        />
      </div>
      {exportActions && (
        <div className="study-fen-actions study-output-actions">
          {exportActions}
        </div>
      )}
    </div>
  );
}

export default OutputPanel;
