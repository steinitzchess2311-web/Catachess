/**
 * Engine Analysis Component
 *
 * Displays Stockfish / cloud engine analysis with:
 * - Multiple principal variations
 * - Score evaluation
 * - Engine spot metrics and health
 * - Analysis controls
 */

import { BoardPosition } from '../types';
import {
  chessAPI,
  EngineAnalysisResult,
  EngineLine,
  EngineHealthInfo,
} from '../utils/api';

export interface EngineAnalysisOptions {
  container: HTMLElement;
  onLineClick?: (line: EngineLine) => void;
  autoRefreshMetrics?: boolean;
  metricsRefreshInterval?: number;
}

const STYLE_ID = 'cata-engine-analysis-styles';

function ensureEngineStyles(): void {
  if (document.getElementById(STYLE_ID)) return;

  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .cata-engine-panel {
      width: 100%;
      min-width: 0;
      display: grid;
      gap: 14px;
      color: #141821;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      container-type: inline-size;
    }

    .cata-engine-shell {
      overflow: hidden;
      border: 1px solid rgba(33, 40, 55, 0.12);
      border-radius: 8px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 248, 251, 0.94)),
        #f7f9fc;
      box-shadow: 0 18px 45px rgba(18, 25, 38, 0.10);
    }

    .cata-engine-top {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 14px;
      border-bottom: 1px solid rgba(33, 40, 55, 0.10);
      background:
        linear-gradient(135deg, rgba(23, 116, 91, 0.11), transparent 46%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(242, 245, 248, 0.88));
    }

    .cata-engine-title {
      min-width: 0;
      display: grid;
      gap: 4px;
    }

    .cata-engine-kicker {
      color: #647083;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .cata-engine-name {
      margin: 0;
      color: #111827;
      font-size: 18px;
      font-weight: 800;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .cata-engine-score {
      min-width: 86px;
      padding: 8px 10px;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 8px;
      background: #111827;
      color: #f8fafc;
      font-variant-numeric: tabular-nums;
      font-size: 22px;
      font-weight: 850;
      line-height: 1;
      text-align: center;
      box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.12);
    }

    .cata-engine-controls {
      display: grid;
      gap: 12px;
      padding: 14px;
    }

    .cata-engine-action-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: center;
    }

    .cata-engine-button {
      min-height: 38px;
      border: 1px solid rgba(19, 111, 88, 0.18);
      border-radius: 8px;
      background: #13745b;
      color: #ffffff;
      cursor: pointer;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0;
      transition:
        transform 140ms ease,
        background-color 140ms ease,
        box-shadow 140ms ease;
      box-shadow: 0 10px 22px rgba(19, 116, 91, 0.20);
    }

    .cata-engine-button:hover,
    .cata-engine-button:focus-visible {
      transform: translateY(-1px);
      background: #0f624d;
      outline: none;
    }

    .cata-engine-button:disabled {
      cursor: not-allowed;
      transform: none;
      background: #a7b0bd;
      box-shadow: none;
    }

    .cata-engine-status {
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 30px;
      padding: 0 10px;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 999px;
      background: #ffffff;
      color: #4b5563;
      white-space: nowrap;
      font-size: 12px;
      font-weight: 750;
    }

    .cata-engine-status::before {
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #94a3b8;
    }

    .cata-engine-status[data-state="ready"]::before,
    .cata-engine-status[data-state="healthy"]::before {
      background: #16a34a;
    }

    .cata-engine-status[data-state="busy"]::before {
      background: #f59e0b;
      animation: cata-engine-pulse 900ms ease-in-out infinite;
    }

    .cata-engine-status[data-state="error"]::before {
      background: #dc2626;
    }

    .cata-engine-settings {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }

    .cata-engine-field {
      display: grid;
      gap: 7px;
      min-width: 0;
    }

    .cata-engine-field-label {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      color: #596579;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .cata-engine-field-value {
      color: #111827;
      font-variant-numeric: tabular-nums;
      letter-spacing: 0;
    }

    .cata-engine-range {
      width: 100%;
      accent-color: #13745b;
    }

    .cata-engine-select {
      width: 100%;
      min-height: 32px;
      border: 1px solid rgba(33, 40, 55, 0.14);
      border-radius: 8px;
      background: #ffffff;
      color: #111827;
      font-size: 12px;
      font-weight: 700;
    }

    .cata-engine-body {
      display: grid;
      gap: 10px;
      padding: 0 14px 14px;
    }

    .cata-engine-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }

    .cata-engine-chip {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      max-width: 100%;
      padding: 0 9px;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.78);
      color: #5f6b7d;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 11px;
      font-weight: 750;
    }

    .cata-engine-notice,
    .cata-engine-empty,
    .cata-engine-error {
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.74);
      padding: 18px 14px;
      color: #647083;
      text-align: center;
      font-size: 13px;
      line-height: 1.45;
    }

    .cata-engine-notice {
      border-color: rgba(217, 119, 6, 0.20);
      background: rgba(255, 251, 235, 0.82);
      color: #92400e;
      text-align: left;
    }

    .cata-engine-error {
      border-color: rgba(220, 38, 38, 0.18);
      background: rgba(254, 242, 242, 0.82);
      color: #991b1b;
    }

    .cata-engine-loading {
      display: grid;
      place-items: center;
      min-height: 128px;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 8px;
      background:
        linear-gradient(90deg, rgba(19, 116, 91, 0.08), transparent 42%, rgba(19, 116, 91, 0.08)),
        rgba(255, 255, 255, 0.72);
      color: #475569;
      font-size: 13px;
      font-weight: 750;
    }

    .cata-engine-lines {
      display: grid;
      gap: 8px;
      max-height: 310px;
      overflow: auto;
      padding-right: 2px;
    }

    .cata-engine-line {
      width: 100%;
      min-width: 0;
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      gap: 10px;
      align-items: start;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 8px;
      background: #ffffff;
      color: inherit;
      cursor: pointer;
      padding: 10px;
      text-align: left;
      transition:
        transform 140ms ease,
        border-color 140ms ease,
        box-shadow 140ms ease;
    }

    .cata-engine-line:hover,
    .cata-engine-line:focus-visible {
      transform: translateY(-1px);
      border-color: rgba(19, 116, 91, 0.28);
      box-shadow: 0 10px 20px rgba(18, 25, 38, 0.08);
      outline: none;
    }

    .cata-engine-rank {
      width: 30px;
      height: 30px;
      display: inline-grid;
      place-items: center;
      border-radius: 8px;
      background: #eef5f2;
      color: #13745b;
      font-size: 12px;
      font-weight: 900;
      font-variant-numeric: tabular-nums;
    }

    .cata-engine-line-main {
      min-width: 0;
      display: grid;
      gap: 7px;
    }

    .cata-engine-line-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: baseline;
    }

    .cata-engine-line-label {
      color: #647083;
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .cata-engine-line-score {
      color: #111827;
      font-size: 18px;
      font-weight: 850;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }

    .cata-engine-line-score[data-score="good"] {
      color: #15803d;
    }

    .cata-engine-line-score[data-score="equal"] {
      color: #b45309;
    }

    .cata-engine-line-score[data-score="bad"] {
      color: #b91c1c;
    }

    .cata-engine-pv {
      min-width: 0;
      color: #384254;
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 12px;
      line-height: 1.48;
      overflow-wrap: anywhere;
    }

    .cata-engine-metrics {
      overflow: hidden;
      border: 1px solid rgba(33, 40, 55, 0.10);
      border-radius: 8px;
      background: #ffffff;
    }

    .cata-engine-metrics-head {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 11px 12px;
      border-bottom: 1px solid rgba(33, 40, 55, 0.08);
    }

    .cata-engine-metrics-title {
      color: #111827;
      font-size: 13px;
      font-weight: 850;
    }

    .cata-engine-spots {
      display: grid;
      gap: 8px;
      padding: 10px;
    }

    .cata-engine-spot {
      display: grid;
      gap: 8px;
      border: 1px solid rgba(33, 40, 55, 0.08);
      border-radius: 8px;
      background: #f8fafc;
      padding: 10px;
    }

    .cata-engine-spot-head,
    .cata-engine-spot-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 8px;
      align-items: center;
    }

    .cata-engine-spot-name {
      min-width: 0;
      overflow: hidden;
      color: #111827;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 12px;
      font-weight: 850;
    }

    .cata-engine-spot-status {
      padding: 4px 7px;
      border-radius: 999px;
      background: #64748b;
      color: #ffffff;
      font-size: 10px;
      font-weight: 900;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .cata-engine-spot-status[data-status="healthy"] {
      background: #15803d;
    }

    .cata-engine-spot-status[data-status="degraded"] {
      background: #b45309;
    }

    .cata-engine-spot-status[data-status="down"] {
      background: #b91c1c;
    }

    .cata-engine-spot-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .cata-engine-metric {
      display: grid;
      gap: 2px;
      color: #647083;
      font-size: 11px;
    }

    .cata-engine-metric strong {
      color: #111827;
      font-size: 12px;
      font-variant-numeric: tabular-nums;
    }

    @container (max-width: 360px) {
      .cata-engine-top,
      .cata-engine-action-row {
        grid-template-columns: 1fr;
      }

      .cata-engine-score {
        width: 100%;
      }

      .cata-engine-settings {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 720px) {
      .cata-engine-shell {
        border-radius: 8px;
        box-shadow: none;
      }

      .cata-engine-top,
      .cata-engine-controls,
      .cata-engine-body {
        padding-left: 12px;
        padding-right: 12px;
      }

      .cata-engine-lines {
        max-height: none;
      }
    }

    @keyframes cata-engine-pulse {
      0%, 100% { opacity: 0.45; transform: scale(0.9); }
      50% { opacity: 1; transform: scale(1.08); }
    }
  `;
  document.head.appendChild(style);
}

export class EngineAnalysis {
  private container: HTMLElement;
  private options: Required<EngineAnalysisOptions>;
  private analysisContainer: HTMLElement;
  private metricsContainer: HTMLElement;
  private controlsContainer: HTMLElement;
  private scoreEl: HTMLElement;
  private statusEl: HTMLElement;
  private currentPosition: BoardPosition | null = null;
  private isAnalyzing: boolean = false;
  private metricsInterval: number | null = null;
  private engineMode: 'cloud' | 'sf' = 'cloud';
  private cloudBlocked: boolean = false;
  private engineNotice: string | null = null;
  private lastResult: EngineAnalysisResult | null = null;

  private depth: number = 15;
  private multipv: number = 3;

  constructor(options: EngineAnalysisOptions) {
    ensureEngineStyles();
    this.container = options.container;
    this.options = {
      ...options,
      onLineClick: options.onLineClick || (() => {}),
      autoRefreshMetrics: options.autoRefreshMetrics ?? true,
      metricsRefreshInterval: options.metricsRefreshInterval || 5000,
    };

    this.analysisContainer = document.createElement('div');
    this.metricsContainer = document.createElement('div');
    this.controlsContainer = document.createElement('div');
    this.scoreEl = document.createElement('div');
    this.statusEl = document.createElement('div');

    this.render();
    this.setupMetricsRefresh();
  }

  private render(): void {
    this.container.innerHTML = '';
    this.container.classList.add('cata-engine-panel');

    const shell = document.createElement('section');
    shell.className = 'cata-engine-shell';
    shell.setAttribute('aria-label', 'Engine analysis');

    const top = document.createElement('div');
    top.className = 'cata-engine-top';

    const titleWrap = document.createElement('div');
    titleWrap.className = 'cata-engine-title';

    const kicker = document.createElement('div');
    kicker.className = 'cata-engine-kicker';
    kicker.textContent = 'Position engine';

    const title = document.createElement('h3');
    title.className = 'cata-engine-name';
    title.textContent = 'Stockfish analysis';

    titleWrap.append(kicker, title);

    this.scoreEl.className = 'cata-engine-score';
    this.scoreEl.textContent = '--';

    top.append(titleWrap, this.scoreEl);

    this.controlsContainer.className = 'cata-engine-controls';
    this.renderControls();

    this.analysisContainer.className = 'cata-engine-body';
    this.metricsContainer.className = 'cata-engine-metrics';

    shell.append(top, this.controlsContainer, this.analysisContainer, this.metricsContainer);
    this.container.appendChild(shell);

    this.renderAnalysis(null);
    this.loadAndRenderMetrics();
  }

  private renderControls(): void {
    this.controlsContainer.innerHTML = '';

    const actionRow = document.createElement('div');
    actionRow.className = 'cata-engine-action-row';

    const analyzeBtn = document.createElement('button');
    analyzeBtn.type = 'button';
    analyzeBtn.className = 'cata-engine-button';
    analyzeBtn.textContent = this.isAnalyzing ? 'Analyzing position' : 'Analyze position';
    analyzeBtn.disabled = this.isAnalyzing || !this.currentPosition;
    analyzeBtn.onclick = () => this.analyze();

    this.statusEl = document.createElement('div');
    this.statusEl.className = 'cata-engine-status';
    this.statusEl.dataset.state = this.isAnalyzing ? 'busy' : this.currentPosition ? 'ready' : 'idle';
    this.statusEl.textContent = this.isAnalyzing
      ? 'Calculating'
      : this.currentPosition
        ? 'Ready'
        : 'No position';

    actionRow.append(analyzeBtn, this.statusEl);

    const settings = document.createElement('div');
    settings.className = 'cata-engine-settings';
    settings.append(
      this.createRangeField('Depth', this.depth, 5, 25, (value) => {
        this.depth = value;
      }),
      this.createRangeField('Lines', this.multipv, 1, 5, (value) => {
        this.multipv = value;
      }),
      this.createEngineField()
    );

    this.controlsContainer.append(actionRow, settings);
  }

  private createRangeField(
    label: string,
    value: number,
    min: number,
    max: number,
    onChange: (value: number) => void
  ): HTMLElement {
    const field = document.createElement('label');
    field.className = 'cata-engine-field';

    const labelRow = document.createElement('span');
    labelRow.className = 'cata-engine-field-label';
    const labelText = document.createElement('span');
    labelText.textContent = label;
    const valueText = document.createElement('span');
    valueText.className = 'cata-engine-field-value';
    valueText.textContent = String(value);
    labelRow.append(labelText, valueText);

    const input = document.createElement('input');
    input.className = 'cata-engine-range';
    input.type = 'range';
    input.min = String(min);
    input.max = String(max);
    input.value = String(value);
    input.oninput = () => {
      const next = Number(input.value);
      valueText.textContent = String(next);
      onChange(next);
    };

    field.append(labelRow, input);
    return field;
  }

  private createEngineField(): HTMLElement {
    const field = document.createElement('label');
    field.className = 'cata-engine-field';

    const labelRow = document.createElement('span');
    labelRow.className = 'cata-engine-field-label';
    const labelText = document.createElement('span');
    labelText.textContent = 'Engine';
    labelRow.appendChild(labelText);

    const select = document.createElement('select');
    select.className = 'cata-engine-select';
    select.value = this.engineMode;

    const cloud = document.createElement('option');
    cloud.value = 'cloud';
    cloud.textContent = 'Lichess Cloud';
    const sf = document.createElement('option');
    sf.value = 'sf';
    sf.textContent = 'SFCata';
    select.append(cloud, sf);

    select.onchange = () => {
      this.engineMode = select.value as 'cloud' | 'sf';
      this.cloudBlocked = false;
      this.engineNotice = null;
      this.lastResult = null;
      this.scoreEl.textContent = '--';
      this.renderControls();
      if (this.currentPosition && !this.isAnalyzing) {
        this.analyze();
      }
    };

    field.append(labelRow, select);
    return field;
  }

  private renderAnalysis(result: EngineAnalysisResult | null): void {
    this.analysisContainer.innerHTML = '';

    if (this.engineNotice) {
      const noticeEl = document.createElement('div');
      noticeEl.className = 'cata-engine-notice';
      noticeEl.textContent = this.engineNotice;
      this.analysisContainer.appendChild(noticeEl);
    }

    if (!result || result.lines.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'cata-engine-empty';
      empty.textContent = this.currentPosition
        ? 'Run analysis to inspect the best continuations from this position.'
        : 'Play or load a position to enable engine analysis.';
      this.analysisContainer.appendChild(empty);
      this.scoreEl.textContent = '--';
      this.scoreEl.style.color = '';
      return;
    }

    this.lastResult = result;
    this.scoreEl.textContent = this.formatScore(result.lines[0].score);
    this.scoreEl.style.color = this.getReadableScoreColor(result.lines[0].score);

    const meta = document.createElement('div');
    meta.className = 'cata-engine-meta';
    if (result.source) {
      meta.appendChild(this.createChip(`Source: ${result.source}`));
    }
    if (result.spotId) {
      meta.appendChild(this.createChip(`Spot: ${result.spotId}`));
    }
    if (meta.childElementCount > 0) {
      this.analysisContainer.appendChild(meta);
    }

    const lines = document.createElement('div');
    lines.className = 'cata-engine-lines';

    result.lines.forEach((line) => {
      const lineEl = document.createElement('button');
      lineEl.type = 'button';
      lineEl.className = 'cata-engine-line';
      lineEl.onclick = () => this.options.onLineClick(line);

      const rank = document.createElement('span');
      rank.className = 'cata-engine-rank';
      rank.textContent = String(line.multipv);

      const main = document.createElement('span');
      main.className = 'cata-engine-line-main';

      const head = document.createElement('span');
      head.className = 'cata-engine-line-head';

      const label = document.createElement('span');
      label.className = 'cata-engine-line-label';
      label.textContent = line.multipv === 1 ? 'Best line' : 'Candidate';

      const score = document.createElement('span');
      score.className = 'cata-engine-line-score';
      score.dataset.score = this.getScoreTone(line.score);
      score.textContent = this.formatScore(line.score);

      const pv = document.createElement('span');
      pv.className = 'cata-engine-pv';
      pv.textContent = line.pv.length > 0 ? this.formatPv(line.pv) : 'No principal variation returned.';

      head.append(label, score);
      main.append(head, pv);
      lineEl.append(rank, main);
      lines.appendChild(lineEl);
    });

    this.analysisContainer.appendChild(lines);
  }

  private createChip(text: string): HTMLElement {
    const chip = document.createElement('span');
    chip.className = 'cata-engine-chip';
    chip.textContent = text;
    return chip;
  }

  private renderMetrics(health: EngineHealthInfo | null): void {
    this.metricsContainer.innerHTML = '';

    const head = document.createElement('div');
    head.className = 'cata-engine-metrics-head';

    const title = document.createElement('div');
    title.className = 'cata-engine-metrics-title';
    title.textContent = 'Engine spots';

    const status = document.createElement('div');
    status.className = 'cata-engine-status';
    status.dataset.state = health ? 'healthy' : 'error';
    status.textContent = health ? 'Online' : 'Unavailable';

    head.append(title, status);
    this.metricsContainer.appendChild(head);

    const spotsWrap = document.createElement('div');
    spotsWrap.className = 'cata-engine-spots';

    if (!health || !health.spots || health.spots.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'cata-engine-empty';
      empty.textContent = health ? 'No engine spots configured.' : 'Engine metrics are unavailable.';
      spotsWrap.appendChild(empty);
      this.metricsContainer.appendChild(spotsWrap);
      return;
    }

    health.spots.forEach((spot) => {
      const spotEl = document.createElement('div');
      spotEl.className = 'cata-engine-spot';

      const spotHead = document.createElement('div');
      spotHead.className = 'cata-engine-spot-head';

      const name = document.createElement('div');
      name.className = 'cata-engine-spot-name';
      name.textContent = `${spot.id}${spot.region ? ` · ${spot.region}` : ''}`;

      const spotStatus = document.createElement('span');
      spotStatus.className = 'cata-engine-spot-status';
      spotStatus.dataset.status = spot.status.toLowerCase();
      spotStatus.textContent = spot.status;

      spotHead.append(name, spotStatus);

      const grid = document.createElement('div');
      grid.className = 'cata-engine-spot-grid';
      grid.append(
        this.createMetric('Latency', `${spot.avg_latency_ms.toFixed(1)}ms`),
        this.createMetric('Success', `${(spot.success_rate * 100).toFixed(1)}%`),
        this.createMetric('Requests', spot.total_requests.toString()),
        this.createMetric('Failures', spot.failure_count.toString())
      );

      spotEl.append(spotHead, grid);
      spotsWrap.appendChild(spotEl);
    });

    this.metricsContainer.appendChild(spotsWrap);
  }

  private createMetric(label: string, value: string): HTMLElement {
    const metric = document.createElement('div');
    metric.className = 'cata-engine-metric';

    const labelEl = document.createElement('span');
    labelEl.textContent = label;

    const valueEl = document.createElement('strong');
    valueEl.textContent = value;

    metric.append(labelEl, valueEl);
    return metric;
  }

  async analyze(): Promise<void> {
    if (!this.currentPosition || this.isAnalyzing) return;
    if (this.engineMode === 'cloud' && this.cloudBlocked) {
      this.engineNotice = 'Cloud evaluation is unavailable for this position. Switch to SFCata to continue.';
      this.renderAnalysis(null);
      return;
    }

    this.isAnalyzing = true;
    this.renderControls();
    this.renderLoading();

    try {
      const result = await chessAPI.analyzePosition(
        this.currentPosition,
        this.depth,
        this.multipv,
        this.engineMode
      );
      if (this.engineMode === 'cloud' && result.source && result.source !== 'CloudEval') {
        this.cloudBlocked = true;
        this.engineNotice = 'Cloud evaluation is unavailable for this position. SFCata is ready as fallback.';
      }
      this.renderAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      if (this.engineMode === 'cloud') {
        this.cloudBlocked = true;
        this.engineNotice = 'Cloud evaluation is unavailable for this position. Switch to SFCata to continue.';
        this.renderAnalysis(null);
      } else {
        const errorEl = document.createElement('div');
        errorEl.className = 'cata-engine-error';
        errorEl.textContent = 'Analysis failed. Please try again.';
        this.analysisContainer.innerHTML = '';
        this.analysisContainer.appendChild(errorEl);
      }
    } finally {
      this.isAnalyzing = false;
      this.renderControls();
    }
  }

  private renderLoading(): void {
    this.analysisContainer.innerHTML = '';
    const loading = document.createElement('div');
    loading.className = 'cata-engine-loading';
    loading.textContent = 'Calculating best continuations';
    this.analysisContainer.appendChild(loading);
  }

  private async loadAndRenderMetrics(): Promise<void> {
    try {
      const health = await chessAPI.getEngineHealth();
      this.renderMetrics(health);
    } catch (error) {
      console.error('Failed to load engine metrics:', error);
      this.renderMetrics(null);
    }
  }

  private setupMetricsRefresh(): void {
    if (this.options.autoRefreshMetrics) {
      this.metricsInterval = window.setInterval(() => {
        this.loadAndRenderMetrics();
      }, this.options.metricsRefreshInterval);
    }
  }

  setPosition(position: BoardPosition): void {
    this.currentPosition = position;
    this.renderControls();
  }

  setMultipv(multipv: number): void {
    this.multipv = multipv;
    this.renderControls();
  }

  private formatPv(pv: string[]): string {
    return pv.slice(0, 14).join(' ') + (pv.length > 14 ? ' ...' : '');
  }

  private formatScore(score: number | string): string {
    if (typeof score === 'string') {
      return score.replace('mate', 'M');
    }
    const pawnScore = score / 100;
    return pawnScore >= 0 ? `+${pawnScore.toFixed(2)}` : pawnScore.toFixed(2);
  }

  private getScoreTone(score: number | string): 'good' | 'equal' | 'bad' {
    if (typeof score === 'string') {
      return score.startsWith('mate-') ? 'bad' : 'good';
    }
    if (score > 50) return 'good';
    if (score < -50) return 'bad';
    return 'equal';
  }

  private getReadableScoreColor(score: number | string): string {
    const tone = this.getScoreTone(score);
    if (tone === 'good') return '#bbf7d0';
    if (tone === 'bad') return '#fecaca';
    return '#fde68a';
  }

  destroy(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }
    this.container.innerHTML = '';
  }
}

export function createEngineAnalysis(
  container: HTMLElement,
  options: Partial<EngineAnalysisOptions> = {}
): EngineAnalysis {
  return new EngineAnalysis({
    container,
    ...options,
  });
}
