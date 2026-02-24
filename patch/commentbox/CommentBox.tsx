import React, { useEffect, useState } from 'react';
import { useStudy } from '../studyContext';
import { ShareSettings } from './ShareSettings/index';
import { OutputPanel } from './OutputPanel';

export function CommentBox() {
  const { state, setComment } = useStudy();
  const currentNode = state.tree.nodes[state.cursorNodeId];

  const [value,     setValue]     = useState(currentNode?.comment || '');
  const [activeTab, setActiveTab] = useState<'comment' | 'output' | 'settings'>('comment');

  useEffect(() => {
    setValue(currentNode?.comment || '');
  }, [currentNode?.comment, state.cursorNodeId]);

  const downloadText = (filename: string, text: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const handleExport = async (scope: 'study' | 'chapter') => {
    try {
      const studyId   = state.studyId;
      const chapterId = state.chapterId;
      if (!studyId || (scope === 'chapter' && !chapterId)) return;
      const base = '/api/v1/workspace/studies/study-patch';
      const url  = scope === 'study'
        ? `${base}/study/${studyId}/pgn-export`
        : `${base}/chapter/${chapterId}/pgn-export`;
      const res  = await fetch(url);
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      const data = await res.json();
      if (!data?.success) throw new Error(data?.error || 'Export failed');
      downloadText(data.filename || `${studyId}-${scope}.pgn`, data.pgn || '');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Export failed');
    }
  };

  return (
    <div className="study-comment-box">
      <div className="study-comment-tabs">
        {(['comment', 'output', 'settings'] as const).map(tab => (
          <button
            key={tab} type="button"
            className={`study-comment-tab${activeTab === tab ? ' is-active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'comment' ? 'Comment' : tab === 'output' ? 'Output' : 'Settings'}
          </button>
        ))}
      </div>

      <div className="study-comment-panel">
        {activeTab === 'settings' ? (
          <ShareSettings />
        ) : activeTab === 'comment' ? (
          <textarea
            className="study-comment-input"
            placeholder="Add comment..."
            value={value}
            onChange={e => {
              const next = e.target.value;
              setValue(next);
              if (state.cursorNodeId) setComment(state.cursorNodeId, next);
            }}
          />
        ) : (
          <OutputPanel
            exportActions={
              <>
                <button
                  type="button"
                  className="study-fen-button study-output-action-btn"
                  onClick={() => handleExport('study')}
                  disabled={!state.studyId}
                >
                  Export Study PGN
                </button>
                <button
                  type="button"
                  className="study-fen-button study-output-action-btn"
                  onClick={() => handleExport('chapter')}
                  disabled={!state.studyId || !state.chapterId}
                >
                  Export Chapter PGN
                </button>
              </>
            }
          />
        )}
      </div>
    </div>
  );
}

export default CommentBox;
