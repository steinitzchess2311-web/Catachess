/**
 * Engine Analysis Component
 *
 * Displays Stockfish engine analysis with:
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
  EngineSpotMetrics,
} from '../utils/api';

export interface EngineAnalysisOptions {
  container: HTMLElement;
  onLineClick?: (line: EngineLine) => void;
  autoRefreshMetrics?: boolean;
  metricsRefreshInterval?: number;
}

export class EngineAnalysis {
  private container: HTMLElement;
  private options: Required<EngineAnalysisOptions>;
  private analysisContainer: HTMLElement;
  private metricsContainer: HTMLElement;
  private controlsContainer: HTMLElement;
  private currentPosition: BoardPosition | null = null;
  private isAnalyzing: boolean = false;
  private metricsInterval: number | null = null;
  private engineMode: 'cloud' | 'sf' = 'cloud';
  private cloudBlocked: boolean = false;
  private engineNotice: string | null = null;

  // Analysis settings
  private depth: number = 15;
  private multipv: number = 3;

  constructor(options: EngineAnalysisOptions) {
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

    this.render();
    this.setupMetricsRefresh();
  }

  /**
   * Render the component
   */
  private render(): void {
    this.container.innerHTML = '';
    this.container.style.cssText = `
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #1e1e1e;
      color: #e0e0e0;
      border-radius: 8px;
      padding: 16px;
      max-width: 400px;
    `;

    // Title
    const title = document.createElement('h3');
    title.textContent = 'Engine Analysis';
    title.style.cssText = `
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
      color: #fff;
    `;
    this.container.appendChild(title);

    // Controls
    this.controlsContainer.style.cssText = `
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    `;
    this.renderControls();
    this.container.appendChild(this.controlsContainer);

    // Analysis results
    this.analysisContainer.style.cssText = `
      margin-bottom: 16px;
      min-height: 200px;
    `;
    this.container.appendChild(this.analysisContainer);

    // Engine metrics
    this.metricsContainer.style.cssText = `
      border-top: 1px solid #333;
      padding-top: 16px;
    `;
    this.container.appendChild(this.metricsContainer);

    // Initial render
    this.renderAnalysis(null);
    this.loadAndRenderMetrics();
  }

  /**
   * Render analysis controls
   */
  private renderControls(): void {
    this.controlsContainer.innerHTML = '';

    // Analyze button
    const analyzeBtn = document.createElement('button');
    analyzeBtn.textContent = this.isAnalyzing ? 'Analyzing...' : 'Analyze Position';
    analyzeBtn.disabled = this.isAnalyzing || !this.currentPosition;
    analyzeBtn.style.cssText = `
      padding: 10px 16px;
      background: ${this.isAnalyzing ? '#555' : '#4caf50'};
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 14px;
      font-weight: 600;
      cursor: ${this.isAnalyzing || !this.currentPosition ? 'not-allowed' : 'pointer'};
      transition: background 0.2s;
    `;
    if (!this.isAnalyzing && this.currentPosition) {
      analyzeBtn.onmouseover = () => (analyzeBtn.style.background = '#45a049');
      analyzeBtn.onmouseout = () => (analyzeBtn.style.background = '#4caf50');
    }
    analyzeBtn.onclick = () => this.analyze();
    this.controlsContainer.appendChild(analyzeBtn);

    // Settings row
    const settingsRow = document.createElement('div');
    settingsRow.style.cssText = `
      display: flex;
      gap: 12px;
      align-items: center;
    `;

    // Depth control
    const depthLabel = document.createElement('label');
    depthLabel.style.cssText = 'flex: 1; font-size: 13px;';
    depthLabel.innerHTML = `
      <div style="margin-bottom: 4px;">Depth: ${this.depth}</div>
      <input type="range" min="5" max="25" value="${this.depth}"
             style="width: 100%;"
             oninput="this.parentElement.firstElementChild.textContent = 'Depth: ' + this.value">
    `;
    const depthInput = depthLabel.querySelector('input') as HTMLInputElement;
    depthInput.oninput = () => {
      this.depth = parseInt(depthInput.value);
    };
    settingsRow.appendChild(depthLabel);

    // MultiPV control
    const multipvLabel = document.createElement('label');
    multipvLabel.style.cssText = 'flex: 1; font-size: 13px;';
    multipvLabel.innerHTML = `
      <div style="margin-bottom: 4px;">Lines: ${this.multipv}</div>
      <input type="range" min="1" max="5" value="${this.multipv}"
             style="width: 100%;"
             oninput="this.parentElement.firstElementChild.textContent = 'Lines: ' + this.value">
    `;
    const multipvInput = multipvLabel.querySelector('input') as HTMLInputElement;
    multipvInput.oninput = () => {
      this.multipv = parseInt(multipvInput.value);
    };
    settingsRow.appendChild(multipvLabel);

    // Engine control
    const engineLabel = document.createElement('label');
    engineLabel.style.cssText = 'flex: 1; font-size: 13px;';
    engineLabel.innerHTML = `
      <div style="margin-bottom: 4px;">Engine</div>
      <select style="width: 100%; padding: 4px;">
        <option value="cloud">Lichess Cloud</option>
        <option value="sf">SFCata</option>
      </select>
    `;
    const engineSelect = engineLabel.querySelector('select') as HTMLSelectElement;
    engineSelect.value = this.engineMode;
    engineSelect.onchange = () => {
      this.engineMode = engineSelect.value as 'cloud' | 'sf';
      this.cloudBlocked = false;
      this.engineNotice = null;
      this.renderControls();
      if (this.currentPosition && !this.isAnalyzing) {
        this.analyze();
      }
    };
    settingsRow.appendChild(engineLabel);

    this.controlsContainer.appendChild(settingsRow);
  }

  /**
   * Render analysis results
   */
  private renderAnalysis(result: EngineAnalysisResult | null): void {
    if (!result || result.lines.length === 0) {
      const message =
        this.engineNotice ||
        (this.currentPosition ? 'Click "Analyze Position" to start' : 'Make a move to analyze');
      const color = this.engineNotice ? '#ff9800' : '#888';
      this.analysisContainer.innerHTML = `
        <div style="
          color: ${color};
          text-align: center;
          padding: 40px 20px;
          font-size: 14px;
        ">
          ${message}
        </div>
      `;
      return;
    }

    this.analysisContainer.innerHTML = '';

    if (this.engineNotice) {
      const noticeEl = document.createElement('div');
      noticeEl.style.cssText = `
        color: #ff9800;
        font-size: 12px;
        margin-bottom: 6px;
      `;
      noticeEl.textContent = this.engineNotice;
      this.analysisContainer.appendChild(noticeEl);
    }

    if (result.source) {
      const sourceInfo = document.createElement('div');
      sourceInfo.style.cssText = `
        color: #999;
        font-size: 12px;
        margin-bottom: 6px;
      `;
      sourceInfo.textContent = `Engine: ${result.source}`;
      this.analysisContainer.appendChild(sourceInfo);
    }

    if (result.spotId) {
      const spotInfo = document.createElement('div');
      spotInfo.style.cssText = `
        color: #999;
        font-size: 12px;
        margin-bottom: 8px;
      `;
      spotInfo.textContent = `Engine spot: ${result.spotId}`;
      this.analysisContainer.appendChild(spotInfo);
    }

    // Analysis lines
    result.lines.forEach((line) => {
      const lineEl = document.createElement('div');
      lineEl.style.cssText = `
        background: #2a2a2a;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: background 0.2s;
      `;
      lineEl.onmouseover = () => (lineEl.style.background = '#333');
      lineEl.onmouseout = () => (lineEl.style.background = '#2a2a2a');
      lineEl.onclick = () => this.options.onLineClick(line);

      // Line header
      const header = document.createElement('div');
      header.style.cssText = `
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-weight: 600;
      `;

      const lineNum = document.createElement('span');
      lineNum.textContent = `Line ${line.multipv}`;
      lineNum.style.color = '#aaa';
      header.appendChild(lineNum);

      const score = document.createElement('span');
      score.textContent = this.formatScore(line.score);
      score.style.cssText = `
        color: ${this.getScoreColor(line.score)};
        font-size: 16px;
      `;
      header.appendChild(score);

      lineEl.appendChild(header);

      // Principal variation
      const pvEl = document.createElement('div');
      pvEl.textContent = line.pv.slice(0, 10).join(' ') + (line.pv.length > 10 ? ' ...' : '');
      pvEl.style.cssText = `
        font-family: 'Courier New', monospace;
        font-size: 12px;
        color: #ccc;
        word-break: break-all;
      `;
      lineEl.appendChild(pvEl);

      this.analysisContainer.appendChild(lineEl);
    });
  }

  /**
   * Render engine metrics
   */
  private renderMetrics(health: EngineHealthInfo | null): void {
    if (!health) {
      this.metricsContainer.innerHTML = `
        <div style="color: #888; font-size: 13px;">
          Engine metrics unavailable
        </div>
      `;
      return;
    }

    this.metricsContainer.innerHTML = '';

    // Metrics title
    const title = document.createElement('div');
    title.textContent = 'Engine Spots';
    title.style.cssText = `
      font-weight: 600;
      margin-bottom: 12px;
      font-size: 14px;
    `;
    this.metricsContainer.appendChild(title);

    if (!health.spots || health.spots.length === 0) {
      const noSpots = document.createElement('div');
      noSpots.textContent = 'No engine spots configured';
      noSpots.style.cssText = 'color: #888; font-size: 13px;';
      this.metricsContainer.appendChild(noSpots);
      return;
    }

    // Spot metrics
    health.spots.forEach((spot) => {
      const spotEl = document.createElement('div');
      spotEl.style.cssText = `
        background: #2a2a2a;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 12px;
      `;

      // Spot header
      const header = document.createElement('div');
      header.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      `;

      const name = document.createElement('span');
      name.textContent = `${spot.id} (${spot.region})`;
      name.style.cssText = 'font-weight: 600;';
      header.appendChild(name);

      const status = document.createElement('span');
      status.textContent = spot.status.toUpperCase();
      status.style.cssText = `
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 600;
        background: ${this.getStatusColor(spot.status)};
        color: white;
      `;
      header.appendChild(status);

      spotEl.appendChild(header);

      // Metrics grid
      const metricsGrid = document.createElement('div');
      metricsGrid.style.cssText = `
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        color: #aaa;
      `;

      const metrics = [
        ['Latency', `${spot.avg_latency_ms.toFixed(1)}ms`],
        ['Success', `${(spot.success_rate * 100).toFixed(1)}%`],
        ['Requests', spot.total_requests.toString()],
        ['Failures', spot.failure_count.toString()],
      ];

      metrics.forEach(([label, value]) => {
        const metric = document.createElement('div');
        metric.innerHTML = `<strong>${label}:</strong> ${value}`;
        metricsGrid.appendChild(metric);
      });

      spotEl.appendChild(metricsGrid);
      this.metricsContainer.appendChild(spotEl);
    });
  }

  /**
   * Analyze current position
   */
  async analyze(): Promise<void> {
    if (!this.currentPosition || this.isAnalyzing) return;
    if (this.engineMode === 'cloud' && this.cloudBlocked) {
      this.engineNotice = 'Cloud Eval unavailable. Please select SFCata engine.';
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
        this.engineNotice = 'Cloud Eval unavailable. Please select SFCata engine.';
      }
      this.renderAnalysis(result);
    } catch (error) {
      console.error('Analysis failed:', error);
      if (this.engineMode === 'cloud') {
        this.cloudBlocked = true;
        this.engineNotice = 'Cloud Eval unavailable. Please select SFCata engine.';
        this.renderAnalysis(null);
      } else {
        this.analysisContainer.innerHTML = `
          <div style="
            color: #f44336;
            text-align: center;
            padding: 20px;
            font-size: 14px;
          ">
            Analysis failed. Please try again.
          </div>
        `;
      }
    } finally {
      this.isAnalyzing = false;
      this.renderControls();
    }
  }

  private renderLoading(): void {
    this.analysisContainer.innerHTML = `
      <div style="
        color: #888;
        text-align: center;
        padding: 20px;
        font-size: 12px;
      ">
        Analyzing...
      </div>
    `;
  }

  /**
   * Load and render engine metrics
   */
  private async loadAndRenderMetrics(): Promise<void> {
    try {
      const health = await chessAPI.getEngineHealth();
      this.renderMetrics(health);
    } catch (error) {
      console.error('Failed to load engine metrics:', error);
      this.renderMetrics(null);
    }
  }

  /**
   * Setup automatic metrics refresh
   */
  private setupMetricsRefresh(): void {
    if (this.options.autoRefreshMetrics) {
      this.metricsInterval = window.setInterval(() => {
        this.loadAndRenderMetrics();
      }, this.options.metricsRefreshInterval);
    }
  }

  /**
   * Update position to analyze
   */
  setPosition(position: BoardPosition): void {
    this.currentPosition = position;
    this.renderControls();
  }

  setMultipv(multipv: number): void {
    this.multipv = multipv;
    this.renderControls();
  }

  /**
   * Format score for display
   */
  private formatScore(score: number | string): string {
    if (typeof score === 'string') {
      // Mate score
      return score.replace('mate', 'M');
    }
    // Centipawn score
    const pawnScore = score / 100;
    return pawnScore >= 0 ? `+${pawnScore.toFixed(2)}` : pawnScore.toFixed(2);
  }

  /**
   * Get color for score
   */
  private getScoreColor(score: number | string): string {
    if (typeof score === 'string') {
      return score.startsWith('mate-') ? '#f44336' : '#4caf50';
    }
    if (score > 200) return '#4caf50';
    if (score > 50) return '#8bc34a';
    if (score > -50) return '#ffc107';
    if (score > -200) return '#ff9800';
    return '#f44336';
  }

  /**
   * Get color for spot status
   */
  private getStatusColor(status: string): string {
    switch (status.toLowerCase()) {
      case 'healthy':
        return '#4caf50';
      case 'degraded':
        return '#ff9800';
      case 'down':
        return '#f44336';
      default:
        return '#888';
    }
  }

  /**
   * Destroy the component
   */
  destroy(): void {
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
    }
    this.container.innerHTML = '';
  }
}

/**
 * Factory function to create EngineAnalysis component
 */
export function createEngineAnalysis(
  container: HTMLElement,
  options: Partial<EngineAnalysisOptions> = {}
): EngineAnalysis {
  return new EngineAnalysis({
    container,
    ...options,
  });
}
