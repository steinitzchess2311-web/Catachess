import React, { useEffect, useRef, useState } from 'react';
import { useStudy } from '../studyContext';
import { ShareSettings } from './ShareSettings/index';
import { OutputPanel } from './OutputPanel';

type ExportStatus =
  | { type: 'idle' }
  | { type: 'loading'; scope: 'study' | 'chapter' }
  | { type: 'success'; message: string }
  | { type: 'warning'; message: string }
  | { type: 'error'; message: string };

export function CommentBox() {
  const { state, setComment } = useStudy();
  const currentNode = state.tree.nodes[state.cursorNodeId];

  const [value,        setValue]        = useState(currentNode?.comment || '');
  const [activeTab,    setActiveTab]    = useState<'comment' | 'output' | 'settings'>('comment');
  const [exportStatus, setExportStatus] = useState<ExportStatus>({ type: 'idle' });
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setValue(currentNode?.comment || '');
  }, [currentNode?.comment, state.cursorNodeId]);

  // Auto-clear non-error toasts after 4 s
  useEffect(() => {
    if (exportStatus.type === 'success' || exportStatus.type === 'warning') {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
      toastTimerRef.current = setTimeout(() => setExportStatus({ type: 'idle' }), 4000);
    }
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, [exportStatus]);

  const downloadText = (filename: string, text: string) => {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const handleExport = async (scope: 'study' | 'chapter') => {
    const studyId   = state.studyId;
    const chapterId = state.chapterId;
    if (!studyId || (scope === 'chapter' && !chapterId)) return;

    setExportStatus({ type: 'loading', scope });
    try {
      const base = '/api/v1/workspace/studies/study-patch';
      const url  = scope === 'study'
        ? `${base}/study/${studyId}/pgn-export`
        : `${base}/chapter/${chapterId}/pgn-export`;

      const res = await fetch(url);
      if (!res.ok) {
        let detail = `Server error ${res.status}`;
        try { const body = await res.json(); detail = body?.detail || body?.error || detail; } catch {}
        throw new Error(detail);
      }

      const data = await res.json();
      if (!data?.success) throw new Error(data?.error || 'Export failed');

      downloadText(data.filename || `${studyId}-${scope}.pgn`, data.pgn || '');

      // Surface a warning if the backend skipped some chapters
      const skipped: Array<{ title: string }> = data.skipped_chapters ?? [];
      if (skipped.length > 0) {
        const names = skipped.map(c => `"${c.title}"`).join(', ');
        setExportStatus({
          type: 'warning',
          message: `Downloaded, but ${skipped.length} chapter${skipped.length > 1 ? 's' : ''} skipped (not yet saved): ${names}`,
        });
      } else {
        setExportStatus({ type: 'success', message: 'Downloaded successfully' });
      }
    } catch (err) {
      setExportStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Export failed',
      });
    }
  };

  const isExporting = exportStatus.type === 'loading';

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
          <>
            <OutputPanel
              exportActions={
                <>
                  <button
                    type="button"
                    className="study-fen-button study-output-action-btn"
                    onClick={() => handleExport('study')}
                    disabled={!state.studyId || isExporting}
                  >
                    {isExporting && exportStatus.scope === 'study' ? 'Exporting…' : 'Export Study PGN'}
                  </button>
                  <button
                    type="button"
                    className="study-fen-button study-output-action-btn"
                    onClick={() => handleExport('chapter')}
                    disabled={!state.studyId || !state.chapterId || isExporting}
                  >
                    {isExporting && exportStatus.scope === 'chapter' ? 'Exporting…' : 'Export Chapter PGN'}
                  </button>
                </>
              }
            />

            {exportStatus.type !== 'idle' && exportStatus.type !== 'loading' && (
              <div className={`study-export-toast study-export-toast--${exportStatus.type}`}>
                <span className="study-export-toast-msg">{exportStatus.message}</span>
                <button
                  type="button"
                  className="study-export-toast-close"
                  onClick={() => setExportStatus({ type: 'idle' })}
                  aria-label="Dismiss"
                >×</button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default CommentBox;
