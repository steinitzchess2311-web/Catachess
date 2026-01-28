import React, { useEffect, useState } from 'react';
import { useStudy } from './studyContext';

export function CommentBox() {
  const { state, setComment } = useStudy();
  const currentNode = state.tree.nodes[state.cursorNodeId];
  const [value, setValue] = useState(currentNode?.comment || '');
  const [activeTab, setActiveTab] = useState<'comment' | 'info'>('comment');
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle');
  const fen = state.currentFen || '';

  useEffect(() => {
    setValue(currentNode?.comment || '');
  }, [currentNode?.comment, state.cursorNodeId]);

  useEffect(() => {
    if (copyState === 'idle') return;
    const timer = window.setTimeout(() => setCopyState('idle'), 1500);
    return () => window.clearTimeout(timer);
  }, [copyState]);

  const handleCopyFen = async () => {
    if (!fen) return;
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(fen);
      } else {
        const temp = document.createElement('textarea');
        temp.value = fen;
        temp.setAttribute('readonly', 'true');
        temp.style.position = 'absolute';
        temp.style.left = '-9999px';
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
      }
      setCopyState('copied');
    } catch {
      setCopyState('error');
    }
  };

  return (
    <div className="study-comment-box">
      <div className="study-comment-tabs">
        <button
          type="button"
          className={`study-comment-tab ${activeTab === 'comment' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('comment')}
        >
          Comment
        </button>
        <button
          type="button"
          className={`study-comment-tab ${activeTab === 'info' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          Info
        </button>
      </div>
      <div className="study-comment-panel">
        {activeTab === 'comment' ? (
          <textarea
            className="study-comment-input"
            placeholder="Add comment..."
            value={value}
            onChange={(e) => {
              const next = e.target.value;
              setValue(next);
              if (state.cursorNodeId) {
                setComment(state.cursorNodeId, next);
              }
            }}
          />
        ) : (
          <div className="study-info-panel">
            <textarea
              className="study-fen-box"
              readOnly
              value={fen || 'FEN unavailable'}
            />
            <div className="study-fen-actions">
              <button
                type="button"
                className="study-fen-button"
                onClick={handleCopyFen}
                disabled={!fen}
              >
                {copyState === 'copied' ? 'Copied' : copyState === 'error' ? 'Copy failed' : 'Copy FEN'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CommentBox;
