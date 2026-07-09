/**
 * Created at: 2026-07-09 02:06 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 02:06 EDT
 * Last Modified by: Codex
 *
 * LargePgnImportModal
 *
 * Handles PGN files that exceed the single-study size threshold (500 KB).
 * Parsing happens in a Web Worker (no UI freeze). Games are grouped into
 * 300 KB batches, each batch becoming one Study inside a new Folder.
 *
 * Flow
 * ────
 * confirm → parsing → preview → importing → done
 *
 * The existing small-file import flow in NewChapterModal is never touched.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@ui/assets/api';
import type { ParsedBatch, ParsedGame } from '../pgn/large-import.worker';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Target raw bytes per Study (300 KB). Worker never splits mid-game. */
const BATCH_SIZE_BYTES = 300_000;

// ---------------------------------------------------------------------------
// Local helpers (duplicated from NewChapterModal intentionally — no shared dep)
// ---------------------------------------------------------------------------

function pgnGameTitle(headers: Record<string, string>): string {
  const white = headers['White'] ?? '?';
  const black = headers['Black'] ?? '?';
  const event = headers['Event'] ?? '';
  if (white === '?' && black === '?' && !event) return 'Imported Game';
  const players = white === '?' && black === '?' ? '' : `${white} vs ${black}`;
  const raw = [players, event].filter(Boolean).join(' – ').replace(/\//g, '-');
  return raw.length > 194 ? raw.slice(0, 194) : raw;
}

function dedupTitles(titles: string[]): string[] {
  const seen = new Map<string, number>();
  return titles.map((t) => {
    const n = (seen.get(t) ?? 0) + 1;
    seen.set(t, n);
    return n === 1 ? t : `${t} (${n})`;
  });
}

function serializeTree(tree: any) {
  const nodes: Record<string, any> = {};
  for (const [id, node] of Object.entries<any>(tree.nodes)) {
    nodes[id] = { ...node, san: node.san ?? '' };
  }
  return { ...tree, nodes };
}

/** Retry on 5xx only, exponential back-off. */
async function withRetry<T>(fn: () => Promise<T>, retries = 2, delayMs = 1000): Promise<T> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await fn();
    } catch (e: any) {
      const status = e?.status ?? 0;
      if (status >= 500 && attempt < retries) {
        await new Promise((r) => setTimeout(r, delayMs * (attempt + 1)));
        continue;
      }
      throw e;
    }
  }
  throw new Error('unreachable');
}

async function runConcurrent<T>(
  tasks: (() => Promise<T>)[],
  limit: number,
  onProgress: (done: number, total: number) => void,
): Promise<PromiseSettledResult<T>[]> {
  const results: PromiseSettledResult<T>[] = new Array(tasks.length);
  let next = 0;
  let done = 0;
  async function pump() {
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
  await Promise.all(Array.from({ length: Math.min(limit, tasks.length) }, pump));
  return results;
}

/** Strip .pgn extension and sanitize for use as a folder / study name. */
function folderNameFromFilename(filename: string): string {
  const base = filename.replace(/\.pgn$/i, '').trim();
  const sanitized = base.replace(/\//g, '-').replace(/\\/g, '-').slice(0, 190).trim();
  return sanitized || 'Imported PGN';
}

// ---------------------------------------------------------------------------
// Phase types
// ---------------------------------------------------------------------------

type Phase =
  | { name: 'confirm' }
  | { name: 'parsing'; parsed: number; total: number }
  | { name: 'preview'; batches: ParsedBatch[]; totalGames: number; skipped: number; folderName: string }
  | { name: 'importing'
      studyIndex: number
      studyTotal: number
      subPhase: 'folder' | 'study' | 'creating' | 'uploading'
      done: number
      total: number
    }
  | { name: 'done'
      folderName: string
      studiesCreated: number
      chaptersImported: number
      chaptersSkipped: number
      errors: string[]
    }
  | { name: 'error'; message: string };

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface LargePgnImportModalProps {
  /** Raw PGN text already read from disk */
  content: string;
  /** Original filename — used to name the new Folder */
  filename: string;
  /** Current study node ID — used to find the parent for the new Folder */
  studyId: string;
  onClose: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function LargePgnImportModal({ content, filename, studyId, onClose }: LargePgnImportModalProps) {
  const [phase, setPhase] = useState<Phase>({ name: 'confirm' });
  const workerRef = useRef<Worker | null>(null);
  const cancelledRef = useRef(false);

  // Clean up worker on unmount
  useEffect(() => {
    return () => {
      cancelledRef.current = true;
      workerRef.current?.terminate();
    };
  }, []);

  // ── Start parsing (called when user clicks "Split & Import") ──────────────
  const startParsing = useCallback(() => {
    cancelledRef.current = false;
    setPhase({ name: 'parsing', parsed: 0, total: 0 });

    const worker = new Worker(
      new URL('../pgn/large-import.worker.ts', import.meta.url),
      { type: 'module' },
    );
    workerRef.current = worker;

    worker.onmessage = (e: MessageEvent) => {
      if (cancelledRef.current) return;

      const msg = e.data as Record<string, any>;

      if (msg.type === 'progress') {
        setPhase({ name: 'parsing', parsed: msg.parsed as number, total: msg.total as number });

      } else if (msg.type === 'done') {
        worker.terminate();
        workerRef.current = null;
        const batches   = msg.batches  as ParsedBatch[];
        const totalGames = msg.totalGames as number;
        const skipped   = msg.skipped   as number;
        const folderName = folderNameFromFilename(filename);
        setPhase({ name: 'preview', batches, totalGames, skipped, folderName });

      } else if (msg.type === 'error') {
        worker.terminate();
        workerRef.current = null;
        setPhase({ name: 'error', message: msg.message as string });
      }
    };

    worker.onerror = (e) => {
      if (cancelledRef.current) return;
      workerRef.current = null;
      setPhase({ name: 'error', message: e.message || 'Worker crashed unexpectedly' });
    };

    worker.postMessage({ type: 'parse', content, batchSizeBytes: BATCH_SIZE_BYTES });
  }, [content, filename]);

  // ── Run the full multi-study import ───────────────────────────────────────
  const startImport = useCallback(async (batches: ParsedBatch[], folderName: string) => {
    const studyTotal = batches.length;
    const allErrors: string[] = [];
    let chaptersImported = 0;
    let chaptersSkipped  = 0;
    let studiesCreated   = 0;

    type ImportSubPhase = 'folder' | 'study' | 'creating' | 'uploading';
    const setImporting = (
      studyIndex: number,
      subPhase: ImportSubPhase,
      done: number,
      total: number,
    ) => {
      if (cancelledRef.current) return;
      setPhase({ name: 'importing', studyIndex, studyTotal, subPhase, done, total });
    };

    // ── 1. Resolve parent node (best-effort; fall back to root) ───────────
    setImporting(0, 'folder', 0, 1);
    let parentId: string | undefined;
    try {
      const node = await api.get(`/api/v1/workspace/nodes/${studyId}`);
      parentId = node?.parent_id ?? undefined;
    } catch {
      // Non-fatal — folder will be created at root level
    }

    // ── 2. Create the Folder ──────────────────────────────────────────────
    let folderId: string;
    try {
      const folder = await withRetry(() =>
        api.post('/api/v1/workspace/nodes', {
          title: folderName,
          node_type: 'folder',
          ...(parentId ? { parent_id: parentId } : {}),
        }),
      );
      if (!folder?.id) throw new Error('No folder id returned');
      folderId = folder.id as string;
    } catch (e: any) {
      setPhase({ name: 'error', message: `Failed to create folder: ${e?.message ?? e}` });
      return;
    }

    // ── 3. Process each batch as one Study ────────────────────────────────
    for (let batchIdx = 0; batchIdx < batches.length; batchIdx++) {
      if (cancelledRef.current) break;

      const batch     = batches[batchIdx];
      const studyName = `${folderName} (${batchIdx + 1})`;

      // 3a. Create Study node
      setImporting(batchIdx + 1, 'study', 0, 1);
      let newStudyId: string;
      try {
        const study = await withRetry(() =>
          api.post('/api/v1/workspace/nodes', {
            title: studyName,
            node_type: 'study',
            parent_id: folderId,
          }),
        );
        if (!study?.id) throw new Error('No study id returned');
        newStudyId = study.id as string;
        studiesCreated++;
      } catch (e: any) {
        allErrors.push(`Study "${studyName}": ${e?.message ?? e}`);
        chaptersSkipped += batch.games.length;
        continue; // skip this batch, try the next
      }

      const games      = batch.games;
      const gameTitles = dedupTitles(games.map((g) => pgnGameTitle(g.headers)));

      // 3b. Phase: Create chapter records (4 concurrent)
      type Created = { id: string; index: number; title: string };
      setImporting(batchIdx + 1, 'creating', 0, games.length);

      const createTasks = games.map((game, i) => () =>
        withRetry(async () => {
          if (game.startingFen) {
            const resp = await api.post('/api/v1/import-export/fen/import', {
              study_id: newStudyId,
              chapter_title: gameTitles[i],
              fen: game.startingFen,
            });
            if (!resp?.chapter_id) throw new Error('No chapter_id');
            return { id: resp.chapter_id as string, index: i, title: gameTitles[i] } as Created;
          } else {
            const resp = await api.post(`/api/v1/workspace/studies/${newStudyId}/chapters`, {
              title: gameTitles[i],
            });
            if (!resp?.id) throw new Error('No chapter id');
            return { id: resp.id as string, index: i, title: gameTitles[i] } as Created;
          }
        }),
      );

      const createResults = await runConcurrent(createTasks, 4, (done, total) => {
        setImporting(batchIdx + 1, 'creating', done, total);
      });

      const created: Created[] = [];
      for (let i = 0; i < createResults.length; i++) {
        const r = createResults[i];
        if (r.status === 'fulfilled') {
          created.push(r.value);
        } else {
          const reason = r.reason;
          allErrors.push(`Create "${gameTitles[i]}": ${reason instanceof Error ? reason.message : String(reason)}`);
          chaptersSkipped++;
        }
      }

      // 3c. Phase: Upload trees (3 concurrent)
      setImporting(batchIdx + 1, 'uploading', 0, created.length);

      const uploadTasks = created.map((ch) => () =>
        withRetry(() =>
          api.put(
            `/api/v1/workspace/studies/study-patch/chapter/${ch.id}/tree`,
            serializeTree(games[ch.index].tree),
          ),
        ),
      );

      const uploadResults = await runConcurrent(uploadTasks, 3, (done, total) => {
        setImporting(batchIdx + 1, 'uploading', done, total);
      });

      for (let i = 0; i < uploadResults.length; i++) {
        if (uploadResults[i].status === 'rejected') {
          const r = uploadResults[i] as PromiseRejectedResult;
          allErrors.push(`Upload "${created[i].title}": ${r.reason instanceof Error ? r.reason.message : String(r.reason)}`);
          chaptersSkipped++;
        } else {
          chaptersImported++;
        }
      }
    } // end batch loop

    if (cancelledRef.current) return;

    setPhase({
      name: 'done',
      folderName,
      studiesCreated,
      chaptersImported,
      chaptersSkipped,
      errors: allErrors,
    });
  }, [studyId]);

  // ── Close guard ───────────────────────────────────────────────────────────
  const handleClose = useCallback(() => {
    if (phase.name === 'parsing' || phase.name === 'importing') {
      if (!window.confirm('Import is in progress. Cancel?')) return;
      cancelledRef.current = true;
      workerRef.current?.terminate();
      workerRef.current = null;
    }
    onClose();
  }, [phase.name, onClose]);

  // ── Render helpers ────────────────────────────────────────────────────────

  const renderBody = () => {
    switch (phase.name) {

      case 'confirm':
        return (
          <>
            <div className="large-pgn-modal-body">
              <p className="large-pgn-modal-copy">
                This file is large and will be split across multiple studies.
              </p>
              <p className="large-pgn-modal-hint">
                A new folder will be created with one study per ~300 KB of content.
                The current study will not be affected.
              </p>
            </div>
            <div className="patch-modal-actions large-pgn-modal-footer">
              <button className="patch-modal-button" onClick={handleClose}>Cancel</button>
              <button className="patch-modal-button primary" onClick={startParsing}>
                Analyze file
              </button>
            </div>
          </>
        );

      case 'parsing': {
        const { parsed, total } = phase;
        const pct = total > 0 ? Math.round((parsed / total) * 100) : 0;
        return (
          <>
            <div className="large-pgn-modal-body large-pgn-modal-body--status">
              <div className="patch-modal-progress patch-modal-progress--large-pgn">
                <div className="patch-modal-progress__meta">
                  <div className="patch-modal-progress__label">
                    {total > 0 ? 'Parsing games' : 'Parsing'}
                  </div>
                  {total > 0 && (
                    <div className="patch-modal-progress__count">{parsed} / {total}</div>
                  )}
                </div>
                <div className="patch-modal-progress__bar">
                  <div
                    className={`patch-modal-progress__fill${total === 0 ? ' is-indeterminate' : ''}`}
                    style={total > 0 ? { width: `${pct}%` } : undefined}
                  />
                </div>
              </div>
            </div>
            <div className="patch-modal-actions large-pgn-modal-footer">
              <button className="patch-modal-button" onClick={handleClose}>Cancel</button>
            </div>
          </>
        );
      }

      case 'preview': {
        const { batches, totalGames, skipped, folderName } = phase;
        return (
          <>
            <div className="large-pgn-modal-body">
              <div className="large-pgn-preview">
                <div className="large-pgn-preview__row">
                  <span>Games found</span>
                  <strong>{totalGames}</strong>
                </div>
                <div className="large-pgn-preview__row">
                  <span>Studies to create</span>
                  <strong>{batches.length}</strong>
                </div>
                <div className="large-pgn-preview__row">
                  <span>Folder name</span>
                  <strong className="large-pgn-preview__folder">{folderName}</strong>
                </div>
                {skipped > 0 && (
                  <div className="large-pgn-preview__warn">
                    {skipped} game{skipped > 1 ? 's' : ''} could not be parsed and will be skipped.
                  </div>
                )}
              </div>
            </div>
            <div className="patch-modal-actions large-pgn-modal-footer">
              <button className="patch-modal-button" onClick={handleClose}>Cancel</button>
              <button
                className="patch-modal-button primary"
                disabled={batches.length === 0}
                onClick={() => startImport(batches, folderName)}
              >
                Split &amp; Import
              </button>
            </div>
          </>
        );
      }

      case 'importing': {
        const { studyIndex, studyTotal, subPhase, done, total } = phase;
        const pct = total > 0 ? Math.round((done / total) * 100) : 0;

        const subLabel: Record<typeof subPhase, string> = {
          folder:   'Creating folder…',
          study:    `Creating study ${studyIndex} of ${studyTotal}…`,
          creating: `Study ${studyIndex}/${studyTotal}: creating chapters… ${done}/${total}`,
          uploading:`Study ${studyIndex}/${studyTotal}: uploading moves… ${done}/${total}`,
        };

        const showBar = subPhase === 'creating' || subPhase === 'uploading';

        return (
          <div className="large-pgn-modal-body large-pgn-modal-body--status">
            <div className="large-pgn-studies-progress">
              {Array.from({ length: studyTotal }, (_, i) => (
                <div
                  key={i}
                  className={`large-pgn-study-dot${
                    i + 1 < studyIndex ? ' done' :
                    i + 1 === studyIndex ? ' active' : ''
                  }`}
                  title={`Study ${i + 1}`}
                />
              ))}
            </div>
            <div className="patch-modal-progress patch-modal-progress--large-pgn">
              <div className="patch-modal-progress__label">{subLabel[subPhase]}</div>
              {showBar && (
                <div className="patch-modal-progress__bar">
                  <div
                    className={`patch-modal-progress__fill${total === 0 ? ' is-indeterminate' : ''}`}
                    style={total > 0 ? { width: `${pct}%` } : undefined}
                  />
                </div>
              )}
            </div>
          </div>
        );
      }

      case 'done': {
        const { folderName, studiesCreated, chaptersImported, chaptersSkipped, errors } = phase;
        const hasErrors = errors.length > 0;
        return (
          <>
            <div className="large-pgn-modal-body">
              <div className="large-pgn-done">
                <div className="large-pgn-done__icon">{hasErrors ? '!' : '✓'}</div>
                <div className="large-pgn-done__summary">
                  <strong>{chaptersImported} chapter{chaptersImported !== 1 ? 's' : ''}</strong> imported
                  into <strong>{studiesCreated} stud{studiesCreated !== 1 ? 'ies' : 'y'}</strong>
                  {' '}in folder <em>"{folderName}"</em>.
                </div>
                {chaptersSkipped > 0 && (
                  <div className="large-pgn-done__skipped">
                    {chaptersSkipped} chapter{chaptersSkipped !== 1 ? 's' : ''} skipped.
                  </div>
                )}
                {hasErrors && (
                  <details className="large-pgn-done__errors">
                    <summary>{errors.length} error{errors.length > 1 ? 's' : ''} - click to expand</summary>
                    <ul>
                      {errors.slice(0, 20).map((e, i) => <li key={i}>{e}</li>)}
                      {errors.length > 20 && <li>...and {errors.length - 20} more</li>}
                    </ul>
                  </details>
                )}
              </div>
            </div>
            <div className="patch-modal-actions large-pgn-modal-footer">
              <button className="patch-modal-button primary" onClick={onClose}>Done</button>
            </div>
          </>
        );
      }

      case 'error':
        return (
          <>
            <div className="large-pgn-modal-body">
              <div className="patch-modal-error">{phase.message}</div>
            </div>
            <div className="patch-modal-actions large-pgn-modal-footer">
              <button className="patch-modal-button" onClick={handleClose}>Close</button>
              <button className="patch-modal-button primary" onClick={startParsing}>
                Retry
              </button>
            </div>
          </>
        );
    }
  };

  const titles: Record<Phase['name'], string> = {
    confirm:   'Large file detected',
    parsing:   'Analyzing PGN…',
    preview:   'Import preview',
    importing: 'Importing…',
    done:      'Import complete',
    error:     'Import failed',
  };

  return (
    <div className="patch-modal-overlay" role="dialog" aria-modal="true">
      <div className="patch-modal patch-modal--large-pgn">
        <h3 className="large-pgn-modal-title">{titles[phase.name]}</h3>
        {renderBody()}
      </div>
    </div>
  );
}
