import { BoardPosition } from '../types';
import { chessAPI, ImitatorResponse } from '../utils/api';

export interface ImitatorPanelOptions {
  container: HTMLElement;
  players?: string[];
}
export class ImitatorPanel {
  private container: HTMLElement;
  private currentPosition: BoardPosition | null = null;
  private selectEl: HTMLSelectElement;
  private resultsEl: HTMLDivElement;

  constructor(options: ImitatorPanelOptions) {
    this.container = options.container;
    this.selectEl = document.createElement('select');
    this.resultsEl = document.createElement('div');
    this.render();
    this.loadPlayers(options.players);
  }

  setPosition(position: BoardPosition): void {
    this.currentPosition = position;
    this.refresh();
  }

  private render(): void {
    this.container.innerHTML = '';
    this.container.style.cssText = `
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #1e1e1e;
      color: #e0e0e0;
      border-radius: 8px;
      padding: 16px;
    `;

    const title = document.createElement('h3');
    title.textContent = 'Imitator';
    title.style.cssText = 'margin: 0 0 12px 0; font-size: 18px; color: #fff;';
    this.container.appendChild(title);

    this.selectEl.style.cssText = 'width: 100%; padding: 8px; margin-bottom: 12px;';
    this.selectEl.addEventListener('change', () => this.refresh());
    this.container.appendChild(this.selectEl);

    this.resultsEl.style.cssText = 'display: flex; flex-direction: column; gap: 8px;';
    this.container.appendChild(this.resultsEl);
  }

  private async loadPlayers(players?: string[]): Promise<void> {
    const list = players?.length ? players : await chessAPI.getImitatorProfiles();
    this.selectEl.innerHTML = list.map((p) => `<option value="${p}">${p}</option>`).join('');
  }

  private async refresh(): Promise<void> {
    if (!this.currentPosition || !this.selectEl.value) return;
    this.resultsEl.innerHTML = 'Loading...';
    try {
      const result: ImitatorResponse = await chessAPI.predictImitator(
        this.currentPosition,
        this.selectEl.value
      );
      this.renderResults(result);
    } catch (error) {
      this.resultsEl.innerHTML = 'Failed to load predictions.';
      console.error(error);
    }
  }

  private renderResults(result: ImitatorResponse): void {
    if (!result.moves.length) {
      this.resultsEl.innerHTML = 'No predictions yet.';
      return;
    }
    const header = `<div style="font-size:12px;color:#bbb;margin-bottom:4px;">
      Likely moves for ${result.player}
    </div>`;
    const cards = result.moves
      .map((move) => {
        const prob = (move.probability * 100).toFixed(1);
        return `
          <div style="background:#2a2a2a;padding:10px;border-radius:6px;">
            <div style="font-weight:600;">${move.move}</div>
            <div style="font-size:12px;color:#bbb;">
              Eval: ${move.engine_eval} · Chance: ${prob}%
            </div>
          </div>
        `;
      })
      .join('');
    this.resultsEl.innerHTML = header + cards;
  }
}

export function createImitatorPanel(
  container: HTMLElement,
  options: Partial<ImitatorPanelOptions> = {}
): ImitatorPanel {
  return new ImitatorPanel({ container, ...options });
}
