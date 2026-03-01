import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';
import { importMultiPgn } from '../pgn/import';
import { LargePgnImportModal } from './LargePgnImportModal';

/** Files above this threshold are handled by LargePgnImportModal instead. */
const LARGE_FILE_THRESHOLD = 500_000;

// ---------------------------------------------------------------------------
// Title helpers
// ---------------------------------------------------------------------------

function pgnGameTitle(headers: Record<string, string>): string {
  const white = headers['White'] ?? '?';
  const black = headers['Black'] ?? '?';
  const event = headers['Event'] ?? '';
  if (white === '?' && black === '?' && !event) return 'Imported Game';
  const players = white === '?' && black === '?' ? '' : `${white} vs ${black}`;
  const raw = [players, event].filter(Boolean).join(' – ')
    .replace(/\//g, '-');  // backend forbids "/" in chapter/study names
  return raw.length > 194 ? raw.slice(0, 194) : raw;
}

/** Append " (2)", " (3)" etc. to repeated titles to satisfy backend uniqueness. */
function dedupTitles(titles: string[]): string[] {
  const seen = new Map<string, number>();
  return titles.map((t) => {
    const n = (seen.get(t) ?? 0) + 1;
    seen.set(t, n);
    return n === 1 ? t : `${t} (${n})`;
  });
}

// ---------------------------------------------------------------------------
// Tree serialization
// ---------------------------------------------------------------------------

/**
 * Serialize a StudyTree for the backend PUT endpoint.
 * The backend requires `san` to be a string; our root node has `san: null`.
 * We replace null with "" so the payload passes schema validation.
 */
function serializeTreeForApi(tree: ReturnType<typeof importMultiPgn>['games'][number]['tree']) {
  const nodes: Record<string, any> = {};
  for (const [id, node] of Object.entries(tree.nodes)) {
    nodes[id] = { ...node, san: node.san ?? '' };
  }
  return { ...tree, nodes };
}

// HTTP helpers
// ---------------------------------------------------------------------------

/** Retry a request on 5xx (server errors). Never retries on 4xx (our data is wrong). */
async function withRetry<T>(fn: () => Promise<T>, retries = 2, delayMs = 1000): Promise<T> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (e: any) {
      const status = e?.response?.status ?? e?.status ?? 0;
      if (status >= 500 && attempt < retries) {
        await new Promise((r) => setTimeout(r, delayMs * (attempt + 1)));
        continue;
      }
      throw e;
    }
  }
  // unreachable but satisfies TypeScript
  throw new Error('unreachable');
}

/**
 * Run tasks with at most `limit` in-flight at once.
 * Each task is individually wrapped with retry logic.
 */
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

  await Promise.all(Array.from({ length: Math.min(limit, tasks.length) }, worker));
  return results;
}

// ---------------------------------------------------------------------------
// Component types
// ---------------------------------------------------------------------------

interface NewChapterModalProps {
  studyId: string;
  nextChapterIndex: number;
  chaptersCount: number;
  existingChapterIds: string[];
  onClose: () => void;
  onCreated: (chapter: any) => void;
  onMultiCreated: (newChapters: any[]) => void;
  onSelectChapter: (chapterId: string) => Promise<void>;
}

type CreateMode = 'empty' | 'fen' | 'pgn';

interface ImportProgress {
  phase: 'parsing' | 'creating' | 'uploading';
  done: number;
  total: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function NewChapterModal({
  studyId,
  nextChapterIndex,
  chaptersCount,
  existingChapterIds,
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

  // Large-file split import
  const [largeFile, setLargeFile] = useState<{ content: string; filename: string } | null>(null);

  const busy = isCreating || isImporting;

  useEffect(() => {
    if (mode !== 'pgn' && titleInputRef.current) {
      titleInputRef.current.focus();
      titleInputRef.current.select();
    }
  }, [mode]);

  // Parse PGN with a "Parsing…" phase so UI stays responsive
  useEffect(() => {
    const text = pgnText.trim();
    if (!text) {
      setPgnParsed(null);
      setProgress(null);
      return;
    }

    // Show parsing indicator immediately, then run on next tick
    setPgnParsed(null);
    setProgress({ phase: 'parsing', done: 0, total: 1 });
    const timer = setTimeout(() => {
      // No upper limit — import everything in the PGN
      setPgnParsed(importMultiPgn(text, 5_000));
      setProgress(null);
    }, 0);
    return () => clearTimeout(timer);
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
      if (!content) return;
      // Large files go through the dedicated split-import flow
      if (content.length > LARGE_FILE_THRESHOLD) {
        setLargeFile({ content, filename: file.name });
      } else {
        setPgnText(content);
      }
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

      const games = pgnParsed.games;
      const errs: string[] = [];

      // Deduplicate titles before any HTTP — concurrent requests must not collide
      const gameTitles = dedupTitles(games.map((g) => pgnGameTitle(g.headers)));

      try {
        // ── Phase 1: Create chapter records (4 concurrent, retry on 5xx) ───
        setProgress({ phase: 'creating', done: 0, total: games.length });
        type Created = { id: string; title: string; index: number };

        const createTasks = games.map((game, i) => () =>
          withRetry(async () => {
            const gameTitle = gameTitles[i];
            if (game.startingFen) {
              const resp = await api.post('/api/v1/import-export/fen/import', {
                study_id: studyId,
                chapter_title: gameTitle,
                fen: game.startingFen,
              });
              if (!resp?.chapter_id) throw new Error('No chapter_id returned');
              return { id: resp.chapter_id, title: gameTitle, index: i } as Created;
            } else {
              const resp = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, {
                title: gameTitle,
              });
              if (!resp?.id) throw new Error('No id returned');
              return { id: resp.id, title: gameTitle, index: i } as Created;
            }
          }),
        );

        const createResults = await runConcurrent(createTasks, 4, (done, total) => {
          setProgress({ phase: 'creating', done, total });
        });

        const created: Created[] = [];
        for (const r of createResults) {
          if (r.status === 'fulfilled') {
            created.push(r.value);
          } else {
            const reason = r.reason;
            const title = gameTitles[createResults.indexOf(r)];
            errs.push(`Create "${title}": ${reason instanceof Error ? reason.message : String(reason)}`);
          }
        }

        // ── Phase 2: Upload trees (3 concurrent, retry on 5xx) ────────────
        // Fewer workers than Phase 1: tree payloads are much larger
        setProgress({ phase: 'uploading', done: 0, total: created.length });

        const uploadTasks = created.map((ch) => () =>
          withRetry(() =>
            api.put(
              `/api/v1/workspace/studies/study-patch/chapter/${ch.id}/tree`,
              serializeTreeForApi(games[ch.index].tree),
            ),
          ),
        );

        const uploadResults = await runConcurrent(uploadTasks, 3, (done, total) => {
          setProgress({ phase: 'uploading', done, total });
        });

        for (let i = 0; i < uploadResults.length; i++) {
          const r = uploadResults[i];
          if (r.status === 'rejected') {
            errs.push(`Upload "${created[i].title}": ${r.reason instanceof Error ? r.reason.message : String(r.reason)}`);
          }
        }

        // ── Phase 3: Fix order on backend (best-effort, silent) ───────────
        if (created.length > 0) {
          const correctOrder = [
            ...existingChapterIds,
            ...created.map((ch) => ch.id),
          ];
          await api.post(
            `/api/v1/workspace/studies/${studyId}/chapters/reorder`,
            { order: correctOrder },
          ).catch(() => { /* non-critical: display is index-based */ });
        }

        // ── Update UI ─────────────────────────────────────────────────────
        const addedChapters = created.map((ch, pos) => ({
          id: ch.id,
          title: ch.title,
          order: chaptersCount + pos,
        }));

        if (addedChapters.length > 0) onMultiCreated(addedChapters);
        if (addedChapters.length > 0) await onSelectChapter(addedChapters[0].id);

        if (errs.length > 0) {
          setError(
            `Imported ${addedChapters.length} of ${games.length} chapter(s).` +
            ` ${errs.length} failed:\n${errs.slice(0, 5).join('\n')}` +
            (errs.length > 5 ? `\n…and ${errs.length - 5} more` : ''),
          );
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
        const chapter = await api.post(`/api/v1/workspace/studies/${studyId}/chapters`, {
          title: nextTitle,
        });
        onCreated(chapter);
        if (chapter?.id) await onSelectChapter(chapter.id);
      }
      onClose();
    } catch (e: any) {
      const detail = e.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join('; '));
      } else {
        setError(detail || e.message || 'Failed to create chapter');
      }
    } finally {
      setIsCreating(false);
    }
  }, [busy, chaptersCount, fen, mode, nextChapterIndex, onClose, onCreated, onMultiCreated, onSelectChapter, pgnParsed, studyId, title]);

  // ── Labels ───────────────────────────────────────────────────────────────

  const progressLabel = (): string => {
    if (!progress) return '';
    if (progress.phase === 'parsing') return 'Parsing PGN…';
    if (progress.phase === 'creating')
      return `Creating chapters… ${progress.done} / ${progress.total}`;
    return `Uploading moves… ${progress.done} / ${progress.total}`;
  };

  const progressPct = (): number => {
    if (!progress || progress.total === 0) return 0;
    if (progress.phase === 'parsing') return 0; // indeterminate
    return Math.round((progress.done / progress.total) * 100);
  };

  const confirmLabel = (): string => {
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

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <>
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
              onChange={(e) => {
                setTitle(e.target.value);
                if (!e.target.value.includes('/')) setTitleError(null);
              }}
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

            {/* Progress — shown during parsing and importing */}
            {progress && (
              <div className="patch-modal-progress">
                <div className="patch-modal-progress__label">{progressLabel()}</div>
                <div className="patch-modal-progress__bar">
                  <div
                    className={`patch-modal-progress__fill${progress.phase === 'parsing' ? ' is-indeterminate' : ''}`}
                    style={progress.phase !== 'parsing' ? { width: `${progressPct()}%` } : undefined}
                  />
                </div>
              </div>
            )}

            {/* Preview — shown after parsing, before import */}
            {!progress && pgnParsed && pgnParsed.games.length > 0 && (
              <div className="patch-modal-pgn-preview">
                <strong>
                  {pgnParsed.games.length === 1
                    ? '1 game found'
                    : `${pgnParsed.games.length} games found`}
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

        {error && (
          <div className="patch-modal-error" style={{ whiteSpace: 'pre-line' }}>{error}</div>
        )}

        <div className="patch-modal-actions">
          <button
            type="button"
            className="patch-modal-button"
            onClick={handleClose}
            disabled={busy}
          >
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

    {/* Large-file split import — rendered outside the regular modal */}
    {largeFile && (
      <LargePgnImportModal
        content={largeFile.content}
        filename={largeFile.filename}
        studyId={studyId}
        onClose={() => setLargeFile(null)}
      />
    )}
    </>
  );
}
