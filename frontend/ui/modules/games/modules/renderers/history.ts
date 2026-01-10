/**
 * History Renderer - Move history display
 */

import type { GameState } from '../core/types.js';

export class HistoryRenderer {
    private moveHistoryList: HTMLElement;

    constructor() {
        this.moveHistoryList = document.getElementById('move-history-list')!;
    }

    render(state: GameState): void {
        const moves = state.position.move_history;

        if (moves.length === 0) {
            this.moveHistoryList.textContent = '';
            return;
        }

        let html = '';
        for (let i = 0; i < moves.length; i += 2) {
            const moveNum = Math.floor(i / 2) + 1;
            const whiteMove = moves[i];
            const blackMove = moves[i + 1] || '';

            html += `<div class="move-pair">
                <span class="move-num">${moveNum}.</span>
                <span class="move-white">${whiteMove}</span>
                ${blackMove ? `<span class="move-black">${blackMove}</span>` : ''}
            </div>`;
        }

        this.moveHistoryList.innerHTML = html;

        // Auto-scroll to bottom
        this.moveHistoryList.scrollTop = this.moveHistoryList.scrollHeight;
    }
}
