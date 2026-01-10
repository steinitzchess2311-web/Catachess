/**
 * Board Renderer - Chess board display
 */

import type { GameState } from '../core/types.js';

export class BoardRenderer {
    private chessBoard: HTMLElement;

    constructor() {
        this.chessBoard = document.getElementById('chess-board')!;
    }

    render(state: GameState): void {
        // Placeholder: Will be replaced with actual chess board rendering
        const fen = state.position.fen;
        const turn = state.position.turn;
        const result = state.position.result;

        this.chessBoard.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div><strong>FEN:</strong></div>
                <div style="font-size: 12px; word-break: break-all; margin: 10px 0;">${fen}</div>
                <div><strong>Turn:</strong> ${turn}</div>
                <div><strong>Result:</strong> ${result}</div>
            </div>
        `;
    }

    renderEmpty(): void {
        this.chessBoard.textContent = 'Connecting to game...';
    }
}
