import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '@ui/assets/api';
import './OpeningTrainerPage.css';

type TrainerMode = 'chapter' | 'merged';
type TrainerColor = 'white' | 'black';
type TrainingMode = 'quiz' | 'learn' | 'preview';
type FeedbackKind = 'success' | 'error' | 'info';

interface EligibilityResponse {
  eligible: boolean;
  reasons: string[];
  stats: {
    total_chapters: number;
    standard_start_chapters: number;
    trainable_chapters: number;
    max_line_ply: number;
    lines_ge_5_ply: number;
  };
}

interface RequiredMove {
  from_fen: string;
  move_san: string;
  move_uci?: string | null;
  color: TrainerColor;
  move_number: number;
  ply: number;
}

interface LeafUnit {
  id: string;
  title: string;
  chapter_id?: string | null;
  line_count: number;
  max_ply: number;
  required_move_count: number;
  required_fens: string[];
  required_moves: RequiredMove[];
  path: string[];
}

interface UnitCatalogResponse {
  study_id: string;
  mode: TrainerMode;
  color: TrainerColor;
  eligibility: EligibilityResponse;
  leaf_units: LeafUnit[];
  total_units: number;
}

interface LineStep {
  from_fen: string;
  to_fen: string;
  move_san: string;
  move_uci?: string | null;
  color: TrainerColor;
  move_number: number;
  ply: number;
}

interface UnitLine {
  signature: string;
  steps: LineStep[];
}

interface UnitDetailResponse {
  study_id: string;
  mode: TrainerMode;
  color: TrainerColor;
  unit: LeafUnit;
  lines: UnitLine[];
}

interface ProgressItem {
  from_fen: string;
  move_san: string;
  color: TrainerColor;
  mastered: boolean;
  correct_count: number;
  wrong_count: number;
  consecutive_correct: number;
}

interface SessionState {
  study_id: string;
  mode: TrainerMode;
  color: TrainerColor;
  training_mode: TrainingMode;
  unit_id: string;
  line_signature: string;
  line_index: number;
  line_count: number;
  step_index: number;
  seed: number;
}

interface PromptMove {
  from_fen: string;
  move_san: string;
  move_uci?: string | null;
  color: TrainerColor;
  move_number: number;
  ply: number;
}

interface AutoMove extends PromptMove {
  to_fen: string;
  reason: string;
}

interface TrainingProgress {
  from_fen: string;
  move_san: string;
  mastered: boolean;
  correct_count: number;
  wrong_count: number;
  consecutive_correct: number;
}

interface StartResponse {
  session: SessionState;
  unit: LeafUnit;
  auto_moves: AutoMove[];
  prompt: PromptMove | null;
  finished: boolean;
}

interface AnswerResponse {
  correct: boolean;
  expected_move_san: string;
  session: SessionState;
  auto_moves: AutoMove[];
  prompt: PromptMove | null;
  finished: boolean;
  progress: TrainingProgress | null;
}

interface ActiveRun {
  session: SessionState;
  unit: LeafUnit;
  prompt: PromptMove | null;
  finished: boolean;
  boardFen: string;
  lastProgress: TrainingProgress | null;
  autoMoves: AutoMove[];
  feedback: string | null;
  feedbackKind: FeedbackKind;
}

function toFenForBoard(fen: string | null | undefined): string {
  const value = (fen || '').trim();
  if (!value) return 'start';
  const fields = value.split(/\s+/);
  if (fields.length === 4) return `${value} 0 1`;
  if (fields.length === 5) return `${value} 1`;
  return value;
}

function progressKey(fromFen: string, moveSan: string): string {
  return `${fromFen}::${moveSan}`;
}

function buildProgressMap(items: ProgressItem[]): Map<string, ProgressItem> {
  const map = new Map<string, ProgressItem>();
  for (const item of items) {
    map.set(progressKey(item.from_fen, item.move_san), item);
  }
  return map;
}

function getUnitMastery(unit: LeafUnit, progressMap: Map<string, ProgressItem>): { mastered: number; total: number } {
  const total = unit.required_moves.length;
  if (total === 0) return { mastered: 0, total: 0 };
  let mastered = 0;
  for (const move of unit.required_moves) {
    const item = progressMap.get(progressKey(move.from_fen, move.move_san));
    if (item?.mastered) mastered += 1;
  }
  return { mastered, total };
}

function toPercent(mastered: number, total: number): number {
  if (total <= 0) return 0;
  return Math.round((mastered / total) * 100);
}

function moveToken(step: { color: TrainerColor; move_number: number; move_san: string }): string {
  return `${step.color === 'white' ? `${step.move_number}.` : `${step.move_number}...`}${step.move_san}`;
}

function readApiError(error: unknown, fallback: string): string {
  const message = (error as { message?: unknown })?.message;
  if (typeof message === 'string' && message.trim() && message !== '[object Object]') {
    return message;
  }
  const detail = (error as { detail?: unknown })?.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail.filter((item): item is string => typeof item === 'string' && item.trim().length > 0);
    if (parts.length > 0) return parts.join(' | ');
  }
  if (detail && typeof detail === 'object') {
    const value = detail as { message?: unknown; reasons?: unknown };
    const detailMessage = typeof value.message === 'string' ? value.message : '';
    const reasons = Array.isArray(value.reasons)
      ? value.reasons.filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
      : [];
    if (detailMessage && reasons.length > 0) {
      return `${detailMessage}: ${reasons.join(' | ')}`;
    }
    if (detailMessage) return detailMessage;
  }
  return fallback;
}

export function OpeningTrainerPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();

  const studyId = id || '';
  const [mode, setMode] = useState<TrainerMode>('chapter');
  const [color, setColor] = useState<TrainerColor>('white');
  const [trainingMode, setTrainingMode] = useState<TrainingMode>('quiz');

  const [eligibility, setEligibility] = useState<EligibilityResponse | null>(null);
  const [units, setUnits] = useState<LeafUnit[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null);
  const [unitDetail, setUnitDetail] = useState<UnitDetailResponse | null>(null);
  const [progressMap, setProgressMap] = useState<Map<string, ProgressItem>>(new Map());
  const [activeRun, setActiveRun] = useState<ActiveRun | null>(null);
  const [answerInput, setAnswerInput] = useState('');
  const [catalogVersion, setCatalogVersion] = useState(0);

  const [loadingEligibility, setLoadingEligibility] = useState(false);
  const [loadingUnits, setLoadingUnits] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [runningAction, setRunningAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const catalogScopeRef = useRef<string>('');
  const unitsRequestSeqRef = useRef(0);
  const detailRequestSeqRef = useRef(0);

  const selectedUnit = useMemo(
    () => units.find((u) => u.id === selectedUnitId) || null,
    [selectedUnitId, units],
  );
  const activeCatalogScope = `${studyId}|${mode}|${color}`;
  const isCatalogReady = catalogScopeRef.current === activeCatalogScope;

  const refreshUnits = useCallback(async () => {
    if (!studyId) return;
    const requestSeq = ++unitsRequestSeqRef.current;
    setLoadingEligibility(true);
    setLoadingUnits(true);
    setError(null);
    catalogScopeRef.current = '';
    detailRequestSeqRef.current += 1;
    setCatalogVersion((prev) => prev + 1);
    setUnits([]);
    setSelectedUnitId(null);
    setActiveRun(null);
    setUnitDetail(null);
    setProgressMap(new Map());
    try {
      const eligibilityData = await api.get(`/api/v1/opening-trainer/studies/${encodeURIComponent(studyId)}/eligibility`) as EligibilityResponse;
      if (requestSeq !== unitsRequestSeqRef.current) return;
      setEligibility(eligibilityData);
      if (!eligibilityData.eligible) {
        catalogScopeRef.current = `${studyId}|${mode}|${color}|blocked`;
        setCatalogVersion((prev) => prev + 1);
        return;
      }

      const data = await api.get(
        `/api/v1/opening-trainer/studies/${encodeURIComponent(studyId)}/units?mode=${mode}&color=${color}`,
      ) as UnitCatalogResponse;
      if (requestSeq !== unitsRequestSeqRef.current) return;
      setEligibility(data.eligibility);
      setUnits(data.leaf_units || []);
      const first = data.leaf_units?.[0]?.id || null;
      setSelectedUnitId((prev) => (prev && data.leaf_units.some((u) => u.id === prev) ? prev : first));
      catalogScopeRef.current = `${studyId}|${mode}|${color}`;
      setCatalogVersion((prev) => prev + 1);

      const fenSet = new Set<string>();
      for (const unit of data.leaf_units || []) {
        for (const fen of unit.required_fens || []) {
          fenSet.add(fen);
        }
      }
      if (fenSet.size > 0) {
        const params = new URLSearchParams();
        params.set('color', color);
        Array.from(fenSet).forEach((fen) => params.append('fens[]', fen));
        const progress = await api.get(`/api/v1/opening-trainer/progress?${params.toString()}`) as { items: ProgressItem[] };
        if (requestSeq !== unitsRequestSeqRef.current) return;
        setProgressMap(buildProgressMap(progress.items || []));
      }
    } catch (e: unknown) {
      if (requestSeq !== unitsRequestSeqRef.current) return;
      setUnits([]);
      setSelectedUnitId(null);
      setError(readApiError(e, 'Failed to load units'));
    } finally {
      if (requestSeq !== unitsRequestSeqRef.current) return;
      setLoadingEligibility(false);
      setLoadingUnits(false);
    }
  }, [studyId, mode, color]);

  useEffect(() => {
    refreshUnits();
  }, [refreshUnits]);

  useEffect(() => {
    const catalogScope = `${studyId}|${mode}|${color}`;
    if (!studyId || !selectedUnitId) {
      detailRequestSeqRef.current += 1;
      setLoadingDetail(false);
      setUnitDetail(null);
      return;
    }
    if (catalogScopeRef.current !== catalogScope) {
      detailRequestSeqRef.current += 1;
      setLoadingDetail(false);
      return;
    }
    const requestSeq = ++detailRequestSeqRef.current;
    setLoadingDetail(true);
    api.get(
      `/api/v1/opening-trainer/studies/${encodeURIComponent(studyId)}/units/${encodeURIComponent(selectedUnitId)}?mode=${mode}&color=${color}`,
    ).then((detail) => {
      if (requestSeq !== detailRequestSeqRef.current) return;
      setUnitDetail(detail as UnitDetailResponse);
    }).catch((e: unknown) => {
      if (requestSeq !== detailRequestSeqRef.current) return;
      const statusCode = (e as { status?: unknown })?.status;
      if (statusCode === 404) {
        setUnitDetail(null);
        if (units.length > 0 && selectedUnitId !== units[0].id) {
          setSelectedUnitId(units[0].id);
        }
        return;
      }
      setError(readApiError(e, 'Failed to load unit detail'));
    }).finally(() => {
      if (requestSeq !== detailRequestSeqRef.current) return;
      setLoadingDetail(false);
    });
  }, [studyId, mode, color, selectedUnitId, catalogVersion, units]);

  const startRun = useCallback(async () => {
    if (
      !studyId ||
      !selectedUnitId ||
      !units.some((unit) => unit.id === selectedUnitId) ||
      !isCatalogReady ||
      loadingUnits ||
      loadingEligibility
    ) {
      return;
    }
    setRunningAction(true);
    setError(null);
    try {
      const response = await api.post(`/api/v1/opening-trainer/studies/${encodeURIComponent(studyId)}/train/start`, {
        mode,
        color,
        training_mode: trainingMode,
        unit_id: selectedUnitId,
      }) as StartResponse;
      const boardFen = toFenForBoard(
        response.prompt?.from_fen || response.auto_moves?.[response.auto_moves.length - 1]?.to_fen || 'start',
      );
      setActiveRun({
        session: response.session,
        unit: response.unit,
        prompt: response.prompt,
        finished: response.finished,
        boardFen,
        lastProgress: null,
        autoMoves: response.auto_moves || [],
        feedback: response.finished ? 'Session complete.' : null,
        feedbackKind: 'info',
      });
      setAnswerInput('');
    } catch (e: unknown) {
      const statusCode = (e as { status?: unknown })?.status;
      if (statusCode === 404) {
        refreshUnits();
      }
      setError(readApiError(e, 'Failed to start training'));
    } finally {
      setRunningAction(false);
    }
  }, [
    studyId,
    selectedUnitId,
    mode,
    color,
    trainingMode,
    units,
    isCatalogReady,
    loadingUnits,
    loadingEligibility,
    refreshUnits,
  ]);

  const submitAnswer = useCallback(async () => {
    if (!studyId || !activeRun || !answerInput.trim()) return;
    setRunningAction(true);
    setError(null);
    try {
      const response = await api.post(`/api/v1/opening-trainer/studies/${encodeURIComponent(studyId)}/train/answer`, {
        session: activeRun.session,
        user_move_san: answerInput.trim(),
      }) as AnswerResponse;

      const boardFen = toFenForBoard(
        response.prompt?.from_fen || response.auto_moves?.[response.auto_moves.length - 1]?.to_fen || activeRun.boardFen,
      );

      if (response.progress) {
        setProgressMap((prev) => {
          const next = new Map(prev);
          next.set(
            progressKey(response.progress.from_fen, response.progress.move_san),
            {
              from_fen: response.progress.from_fen,
              move_san: response.progress.move_san,
              color: activeRun.session.color,
              mastered: response.progress.mastered,
              correct_count: response.progress.correct_count,
              wrong_count: response.progress.wrong_count,
              consecutive_correct: response.progress.consecutive_correct,
            },
          );
          return next;
        });
      }

      setActiveRun((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          session: response.session,
          prompt: response.prompt,
          finished: response.finished,
          boardFen,
          lastProgress: response.progress || prev.lastProgress,
          autoMoves: response.auto_moves || [],
          feedback: response.correct ? 'Correct move.' : `Expected: ${response.expected_move_san}`,
          feedbackKind: response.correct ? 'success' : 'error',
        };
      });
      setAnswerInput('');
    } catch (e: unknown) {
      setError(readApiError(e, 'Failed to submit answer'));
    } finally {
      setRunningAction(false);
    }
  }, [studyId, activeRun, answerInput]);

  const selectedUnitMastery = useMemo(() => {
    if (!selectedUnit) return { mastered: 0, total: 0 };
    return getUnitMastery(selectedUnit, progressMap);
  }, [selectedUnit, progressMap]);

  const allUnitsMastery = useMemo(() => {
    let mastered = 0;
    let total = 0;
    for (const unit of units) {
      const item = getUnitMastery(unit, progressMap);
      mastered += item.mastered;
      total += item.total;
    }
    return { mastered, total, percent: toPercent(mastered, total) };
  }, [units, progressMap]);

  const selectedMasteryPercent = useMemo(
    () => toPercent(selectedUnitMastery.mastered, selectedUnitMastery.total),
    [selectedUnitMastery],
  );

  const sessionLinePercent = useMemo(() => {
    if (!activeRun) return 0;
    const currentLine = Math.min(activeRun.session.line_count, activeRun.session.line_index + 1);
    return toPercent(currentLine, Math.max(1, activeRun.session.line_count));
  }, [activeRun]);

  return (
    <div className="ot-page">
      <div className="ot-bg-shape ot-bg-shape-a" />
      <div className="ot-bg-shape ot-bg-shape-b" />
      <header className="ot-topbar">
        <button type="button" className="ot-back" onClick={() => navigate(-1)}>
          Back to Study
        </button>
        <div className="ot-title-wrap">
          <p className="ot-kicker">Opening Trainer</p>
          <h1>Repertoire Flight Deck</h1>
          <p className="ot-study-tag">Study {studyId ? `#${studyId.slice(0, 8)}` : '#N/A'}</p>
        </div>
        <div className="ot-controls">
          <label>
            Mode
            <select value={mode} onChange={(e) => setMode(e.target.value as TrainerMode)}>
              <option value="chapter">Chapter</option>
              <option value="merged">Merged</option>
            </select>
          </label>
          <label>
            Color
            <select value={color} onChange={(e) => setColor(e.target.value as TrainerColor)}>
              <option value="white">White</option>
              <option value="black">Black</option>
            </select>
          </label>
          <label>
            Training
            <select value={trainingMode} onChange={(e) => setTrainingMode(e.target.value as TrainingMode)}>
              <option value="quiz">Quiz</option>
              <option value="learn">Learn</option>
              <option value="preview">Preview</option>
            </select>
          </label>
        </div>
      </header>

      <section className="ot-metric-strip">
        <article className="ot-metric-card">
          <span>Trainable Chapters</span>
          <strong>{eligibility ? eligibility.stats.trainable_chapters : '--'}</strong>
          <small>{eligibility ? `of ${eligibility.stats.total_chapters} total` : 'loading eligibility'}</small>
        </article>
        <article className="ot-metric-card">
          <span>Global Mastery</span>
          <strong>{allUnitsMastery.percent}%</strong>
          <small>{allUnitsMastery.mastered}/{allUnitsMastery.total} moves</small>
        </article>
        <article className="ot-metric-card">
          <span>Selected Unit</span>
          <strong>{selectedMasteryPercent}%</strong>
          <small>{selectedUnitMastery.mastered}/{selectedUnitMastery.total} mastered</small>
        </article>
        <article className="ot-metric-card">
          <span>Max Line Depth</span>
          <strong>{eligibility ? eligibility.stats.max_line_ply : '--'}</strong>
          <small>{units.length} trainable units</small>
        </article>
      </section>

      {error && <div className="ot-alert">{error}</div>}

      <main className="ot-layout">
        <section className="ot-panel ot-panel-left">
          <div className="ot-panel-head">
            <h2>Units</h2>
            {(loadingUnits || loadingEligibility) && <span>Loading...</span>}
          </div>

          {eligibility && !eligibility.eligible ? (
            <div className="ot-blocked">
              <h3>Study Not Ready</h3>
              <ul>
                {eligibility.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="ot-unit-list">
              {units.map((unit) => {
                const mastery = getUnitMastery(unit, progressMap);
                const ratio = toPercent(mastery.mastered, mastery.total);
                return (
                  <button
                    type="button"
                    key={unit.id}
                    className={`ot-unit-card${unit.id === selectedUnitId ? ' is-active' : ''}`}
                    onClick={() => {
                      setSelectedUnitId(unit.id);
                      setActiveRun(null);
                    }}
                  >
                    <div className="ot-unit-title">{unit.title}</div>
                    {unit.path?.length > 0 && <div className="ot-unit-path">{unit.path.join(' / ')}</div>}
                    <div className="ot-unit-meta">
                      <span>{unit.line_count} lines</span>
                      <span>{unit.required_move_count} moves</span>
                      <span>ply {unit.max_ply}</span>
                    </div>
                    <div className="ot-progress-row">
                      <div className="ot-progress-track">
                        <div className="ot-progress-fill" style={{ width: `${ratio}%` }} />
                      </div>
                      <span>{mastery.mastered}/{mastery.total}</span>
                    </div>
                  </button>
                );
              })}
              {units.length === 0 && !loadingUnits && (
                <div className="ot-empty">No trainable units yet.</div>
              )}
            </div>
          )}
        </section>

        <section className="ot-panel ot-panel-main">
          <div className="ot-panel-head">
            <h2>Training</h2>
            <button
              type="button"
              className="ot-start"
              disabled={
                !selectedUnitId ||
                runningAction ||
                loadingUnits ||
                loadingEligibility ||
                !isCatalogReady ||
                !!(eligibility && !eligibility.eligible)
              }
              onClick={startRun}
            >
              {runningAction ? 'Processing...' : activeRun ? 'Restart Session' : 'Start Session'}
            </button>
          </div>

          <div className="ot-main-grid">
            <div className="ot-board-card">
              <Chessboard
                id="opening-trainer-board"
                position={activeRun ? activeRun.boardFen : 'start'}
                arePiecesDraggable={false}
                boardOrientation={color}
                customDarkSquareStyle={{ backgroundColor: '#4f7ccf' }}
                customLightSquareStyle={{ backgroundColor: '#eef4ff' }}
              />
              <div className="ot-board-caption">
                <span>{color === 'white' ? 'White Repertoire' : 'Black Repertoire'}</span>
                {activeRun?.session.line_signature && <code>{activeRun.session.line_signature.slice(0, 18)}</code>}
              </div>
            </div>

            <div className="ot-session-card">
              {!activeRun ? (
                <div className="ot-session-empty">
                  Pick a unit and start a session.
                </div>
              ) : (
                <>
                  <div className="ot-session-chips">
                    <span>{activeRun.session.mode}</span>
                    <span>{activeRun.session.color}</span>
                    <span>{activeRun.session.training_mode}</span>
                  </div>

                  <div className="ot-session-progress-head">
                    <span>
                      Line {Math.min(activeRun.session.line_count, activeRun.session.line_index + 1)} / {activeRun.session.line_count}
                    </span>
                    <span>Step {activeRun.session.step_index}</span>
                  </div>
                  <div className="ot-session-progress-track">
                    <div className="ot-session-progress-fill" style={{ width: `${sessionLinePercent}%` }} />
                  </div>

                  <div className="ot-session-line">
                    <span>Unit</span>
                    <strong>{activeRun.unit.title}</strong>
                  </div>
                  <div className="ot-session-line">
                    <span>Status</span>
                    <strong>{activeRun.finished ? 'Completed' : 'In progress'}</strong>
                  </div>
                  <div className="ot-session-line">
                    <span>Mastery</span>
                    <strong>{selectedUnitMastery.mastered}/{selectedUnitMastery.total}</strong>
                  </div>

                  {activeRun.prompt && (
                    <div className="ot-prompt-box">
                      <p>Your move ({activeRun.prompt.color})</p>
                      <div>
                        Move {activeRun.prompt.move_number} ({activeRun.prompt.ply} ply)
                      </div>
                    </div>
                  )}

                  {!activeRun.finished && activeRun.prompt && (
                    <>
                      <div className="ot-answer-row">
                        <input
                          value={answerInput}
                          onChange={(e) => setAnswerInput(e.target.value)}
                          placeholder="Enter SAN (e.g. Nf3)"
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') submitAnswer();
                          }}
                        />
                        <button type="button" disabled={runningAction || !answerInput.trim()} onClick={submitAnswer}>
                          Submit
                        </button>
                      </div>
                      <div className="ot-answer-hint">Use SAN only. Press Enter to submit quickly.</div>
                    </>
                  )}

                  {activeRun.feedback && (
                    <div className={`ot-feedback${activeRun.feedbackKind === 'success' ? ' is-success' : activeRun.feedbackKind === 'error' ? ' is-error' : ''}`}>
                      {activeRun.feedback}
                    </div>
                  )}

                  {activeRun.lastProgress && (
                    <div className="ot-progress-stats">
                      <span>Streak: {activeRun.lastProgress.consecutive_correct}</span>
                      <span>Correct: {activeRun.lastProgress.correct_count}</span>
                      <span>Wrong: {activeRun.lastProgress.wrong_count}</span>
                    </div>
                  )}

                  {activeRun.autoMoves.length > 0 && (
                    <div className="ot-auto-box">
                      <p>System Continuation</p>
                      <div className="ot-auto-moves">
                        {activeRun.autoMoves.map((autoMove, idx) => (
                          <span key={`${autoMove.to_fen}-${idx}`}>{moveToken(autoMove)}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </section>

        <section className="ot-panel ot-panel-right">
          <div className="ot-panel-head">
            <h2>Line Preview</h2>
            <span>{loadingDetail ? 'Loading...' : unitDetail ? `${unitDetail.lines.length} lines` : 'Idle'}</span>
          </div>
          {unitDetail ? (
            <div className="ot-line-list">
              {unitDetail.lines.map((line) => (
                <div className="ot-line-card" key={line.signature}>
                  <div className="ot-line-head">
                    <div className="ot-line-label">{line.signature.slice(0, 12)}</div>
                    <span>{line.steps.length} ply</span>
                  </div>
                  <div className="ot-line-moves">
                    {line.steps.map((step, idx) => (
                      <span key={`${line.signature}-${idx}`}>
                        {moveToken(step)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
              {unitDetail.lines.length === 0 && <div className="ot-empty">No lines</div>}
            </div>
          ) : (
            <div className="ot-empty">Select a unit to inspect lines.</div>
          )}
        </section>
      </main>
    </div>
  );
}

export default OpeningTrainerPage;
