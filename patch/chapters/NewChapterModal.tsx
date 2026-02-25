import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';
import { importMultiPgn } from '../pgn/import';

function pgnGameTitle(headers: Record<string, string>): string {
  const white = headers['White'] ?? '?';
  const black = headers['Black'] ?? '?';
  const event = headers['Event'] ?? '';
  if (white === '?' && black === '?' && !event) return 'Imported Game';
  const players = white === '?' && black === '?' ? '' : `${white} vs ${black}`;
  return [players, event].filter(Boolean).join(' – ');
}

// ---------------------------------------------------------------------------
// Concurrent task runner — at most `limit` promises in flight at once
// ---------------------------------------------------------------------------
async function runConcurrent<T>(
  tasks: (() => Promise<T>)[],
  limit: number,
  onProgress: (done: number, total: number) => void,
): Promise<PromiseSettledResult<T>[]> {
  const results: PromiseSettledResult<T>[] = new Array(tasks.length);
  let next = 0;
  let done = 0;

  async function worker() {
    while (next < tasks.length) {
      const i = next++;
      try {
        results[i] = { status: 'fulfilled', value: await tasks[i]() };
      } catch (e) {
        results[i] = { status: 'rejected', reason: e };
      }
      onProgress(++done, tasks.length);
    }
  }

  const workers = Array.from({ length: Math.min(limit, tasks.length) }, () => worker());
  await Promise.all(workers);
  return results;
}

interface NewChapterModalProps {
  studyId: string;
  nextChapterIndex: number;
  chaptersCount: number;
  onClose: () => void;
  /** Called when a single chapter (empty/fen) is created. */
  onCreated: (chapter: any) => void;
  /** Called when multiple chapters are created from a PGN. */
  onMultiCreated: (newChapters: any[]) => void;
  /** Load + select the given chapter tree (from useChapters.handleSelectChapter). */
  onSelectChapter: (chapterId: string) => Promise<void>;
}

type CreateMode = 'empty' | 'fen' | 'pgn';

interface ImportProgress {
  phase: 'creating' | 'uploading';
  done: number;
  total: number;
}

export function NewChapterModal({
  studyId,
  nextChapterIndex,
  chaptersCount,
  onClose,
  onCreated,
  onMultiCreated,
  onSelectChapter,
}: NewChapterModalProps) {
  const [mode, setMode] = useState<CreateMode>('empty');
  const [title, setTitle] = useState(`Chapter ${nextChapterIndex}`);
  const [titleError, setTitleError] = useState<string | null>(null);
  const [fen, setFen] = useState('');
  const [pgnText, setPgnText] = useState('');
  const [pgnParsed, setPgnParsed] = useState<ReturnType<typeof importMultiPgn> | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [progress, setProgress] = useState<ImportProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const titleInputRef = useRef<HTMLInputElement | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const busy = isCreating || isImporting;

  useEffect(() => {
    if (mode !== 'pgn' && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [mode]);

  useEffect(() => {
    const text = pgnText.trim();
    if (!text) { setPgnParsed(null); return; }
    setPgnParsed(importMultiPgn(text, 64));
  }, [pgnText]);

  const handleClose = useCallback(() => {
    if (busy) return;
    onClose();
  }, [busy, onClose]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      if (content) setPgnText(content);
    };
    reader.readAsText(file);
    e.target.value = '';
  }, []);

  const handleConfirm = useCallback(async () => {
    if (busy) return;
    setError(null);

    // ── PGN import ──────────────────────────────────────────────────────────
    if (mode === 'pgn') {
      if (!pgnParsed || pgnParsed.games.length === 0) return;
      setIsImporting(true);
      setProgress({ phase: 'creating', done: 0, total: pgnParsed.games.length });

      const games = pgnParsed.games;
      const errs: string[] = [];

      try {
        // ── Phase 1: Create all chapters concurrently (8 in parallel) ──────
        type ChapterResult = { id: string; title: string; index: number } | null;

        const createTasks = games.map((game, i) => async (): Promise<ChapterResult> => {
          const gameTitle = pgnGameTitle(game.headers);
          try {
            if (game.startingFen) {
              const resp = await api.post('/api/v1/import-export/fen/import', {
                study_id: studyId,
                chapter_title: gameTitle,
                fen: game.startingFen,
              });
              return resp?.chapter_id ? { id: resp.chapter_id, title: gameTitle, index: i } : null;
            } else {
              const resp = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, { title: gameTitle });
              return resp?.id ? { id: resp.id, title: gameTitle, index: i } : null;
            }
          } catch (e) {
            errs.push(`Create "${gameTitle}": ${e instanceof Error ? e.message : 'error'}`);
            return null;
          }
        });

        const createResults = await runConcurrent(createTasks, 8, (done, total) => {
          setProgress({ phase: 'creating', done, total });
        });

        // Collect successful chapters (preserve order)
        const created: Array<{ id: string; title: string; index: number }> = [];
        for (const r of createResults) {
          if (r.status === 'fulfilled' && r.value) created.push(r.value);
        }

        // ── Phase 2: Upload trees concurrently (8 in parallel) ────────────
        setProgress({ phase: 'uploading', done: 0, total: created.length });

        const uploadTasks = created.map((ch) => async () => {
          try {
            await api.put(
              `/api/v1/workspace/studies/study-patch/chapter/${ch.id}/tree`,
              games[ch.index].tree,
            );
          } catch (e) {
            errs.push(`Upload tree "${ch.title}": ${e instanceof Error ? e.message : 'error'}`);
          }
        });

        await runConcurrent(uploadTasks, 8, (done, total) => {
          setProgress({ phase: 'uploading', done, total });
        });

        // ── Update UI with successfully created chapters ───────────────────
        const addedChapters = created.map((ch, pos) => ({
          id: ch.id,
          title: ch.title,
          order: chaptersCount + pos,
        }));

        if (addedChapters.length > 0) onMultiCreated(addedChapters);
        if (addedChapters.length > 0) await onSelectChapter(addedChapters[0].id);

        if (errs.length > 0) {
          setError(`Imported ${addedChapters.length} chapter(s) with ${errs.length} error(s):\n${errs.join('\n')}`);
          return;
        }
      } finally {
        setIsImporting(false);
        setProgress(null);
      }

      onClose();
      return;
    }

    // ── Empty / FEN ─────────────────────────────────────────────────────────
    const nextTitle = title.trim() || `Chapter ${nextChapterIndex}`;
    if (nextTitle.includes('/')) { setTitleError('No "/" allowed in chapter name'); return; }
    const trimmedFen = mode === 'fen' ? fen.trim() : '';

    setIsCreating(true);
    try {
      if (trimmedFen) {
        const resp = await api.post('/api/v1/import-export/fen/import', {
          study_id: studyId,
          chapter_title: nextTitle,
          fen: trimmedFen,
        });
        const chapter = {
          id: resp.chapter_id,
          title: nextTitle,
          order: chaptersCount,
          starting_fen: resp.starting_fen,
        };
        onCreated(chapter);
        if (chapter.id) await onSelectChapter(chapter.id);
      } else {
        const chapter = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, { title: nextTitle });
        onCreated(chapter);
        if (chapter?.id) await onSelectChapter(chapter.id);
      }
      onClose();
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join('; '));
      } else {
        setError(detail || e.message || 'Failed to create chapter');
      }
    } finally {
      setIsCreating(false);
    }
  }, [busy, chaptersCount, fen, mode, nextChapterIndex, onClose, onCreated, onMultiCreated, onSelectChapter, pgnParsed, studyId, title]);

  const confirmLabel = () => {
    if (mode === 'pgn') {
      if (isImporting) return 'Importing…';
      if (pgnParsed && pgnParsed.games.length > 0)
        return `Import ${pgnParsed.games.length} game${pgnParsed.games.length > 1 ? 's' : ''}`;
      return 'Import';
    }
    return isCreating ? 'Creating…' : 'Create';
  };

  const confirmDisabled =
    busy ||
    (mode === 'pgn' && (!pgnParsed || pgnParsed.games.length === 0));

  return (
    <div className="patch-modal-overlay" role="dialog" aria-modal="true">
      <div className="patch-modal">
        <h3>New Chapter</h3>

        <div className="patch-modal-tabs">
          {(['empty', 'fen', 'pgn'] as const).map((m) => (
            <button
              key={m}
              type="button"
              className={`patch-modal-tab${mode === m ? ' is-active' : ''}`}
              onClick={() => { setMode(m); setError(null); setTitleError(null); }}
              disabled={busy}
            >
              {m === 'empty' ? 'Empty' : m === 'fen' ? 'From FEN' : 'From PGN'}
            </button>
          ))}
        </div>

        {mode !== 'pgn' && (
          <>
            <label className="patch-modal-label">Chapter Title</label>
            <input
              ref={titleInputRef}
              className="patch-modal-input"
              value={title}
              onChange={(e) => { setTitle(e.target.value); if (!e.target.value.includes('/')) setTitleError(null); }}
              onFocus={(e) => e.target.select()}
              placeholder="Chapter 1"
            />
            {titleError && <div className="patch-modal-error">{titleError}</div>}
          </>
        )}

        {mode === 'fen' && (
          <>
            <label className="patch-modal-label">Starting Position (FEN)</label>
            <textarea
              className="patch-modal-textarea"
              value={fen}
              onChange={(e) => setFen(e.target.value)}
              placeholder="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
              rows={2}
            />
            <div className="patch-modal-hint-text">
              Enter a FEN string to start from a custom position (endgames, puzzles, etc.)
            </div>
          </>
        )}

        {mode === 'pgn' && (
          <>
            <textarea
              className="patch-modal-textarea patch-modal-textarea--pgn"
              value={pgnText}
              onChange={(e) => setPgnText(e.target.value)}
              placeholder="Paste PGN here…"
              spellCheck={false}
              rows={8}
              disabled={busy}
            />
            <div className="patch-modal-pgn-actions">
              <button
                type="button"
                className="patch-modal-button"
                onClick={() => fileRef.current?.click()}
                disabled={busy}
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
              {pgnText && !busy && (
                <button
                  type="button"
                  className="patch-modal-button"
                  onClick={() => { setPgnText(''); setPgnParsed(null); }}
                >
                  Clear
                </button>
              )}
            </div>

            {/* Progress bar */}
            {progress && (
              <div className="patch-modal-progress">
                <div className="patch-modal-progress__label">
                  {progress.phase === 'creating'
                    ? `Creating chapters… ${progress.done} / ${progress.total}`
                    : `Uploading trees… ${progress.done} / ${progress.total}`}
                </div>
                <div className="patch-modal-progress__bar">
                  <div
                    className="patch-modal-progress__fill"
                    style={{ width: `${Math.round((progress.done / progress.total) * 100)}%` }}
                  />
                </div>
              </div>
            )}

            {!progress && pgnParsed && pgnParsed.games.length > 0 && (
              <div className="patch-modal-pgn-preview">
                <strong>
                  {pgnParsed.games.length === 1
                    ? '1 game found'
                    : `${pgnParsed.games.length} games found${pgnParsed.truncated ? ' (truncated to 64)' : ''}`}
                </strong>
                <div className="patch-modal-pgn-preview__first">
                  {pgnGameTitle(pgnParsed.games[0].headers)}
                  {pgnParsed.games[0].startingFen && <span> · Custom starting position</span>}
                </div>
              </div>
            )}
            {!progress && pgnParsed && pgnParsed.games.length === 0 && (
              <div className="patch-modal-error">No valid PGN games found.</div>
            )}
          </>
        )}

        {error && <div className="patch-modal-error" style={{ whiteSpace: 'pre-line' }}>{error}</div>}

        <div className="patch-modal-actions">
          <button type="button" className="patch-modal-button" onClick={handleClose} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            className="patch-modal-button primary"
            onClick={handleConfirm}
            disabled={confirmDisabled}
          >
            {confirmLabel()}
          </button>
        </div>
      </div>
    </div>
  );
}
