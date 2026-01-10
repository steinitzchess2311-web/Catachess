/**
 * Info Renderer - Game meta and player info
 */

import type { GameState } from '../core/types.js';

export class InfoRenderer {
    private gameMeta: HTMLElement;
    private playerInfo: HTMLElement;

    constructor() {
        this.gameMeta = document.getElementById('game-meta')!;
        this.playerInfo = document.getElementById('player-info')!;
    }

    render(state: GameState): void {
        this.renderGameMeta(state);
        this.renderPlayerInfo(state);
    }

    private renderGameMeta(state: GameState): void {
        const status = state.state.charAt(0).toUpperCase() + state.state.slice(1);
        const moveNum = state.position.move_number;

        this.gameMeta.innerHTML = `
            <div><strong>Game ID:</strong> ${state.game_id}</div>
            <div><strong>Status:</strong> ${status}</div>
            <div><strong>Move:</strong> ${moveNum}</div>
        `;
    }

    private renderPlayerInfo(state: GameState): void {
        const players = Object.values(state.players);
        const whitePlayer = players.find(p => p.color === 'white');
        const blackPlayer = players.find(p => p.color === 'black');

        this.playerInfo.innerHTML = `
            <div class="player-row">
                <strong>⚪ White:</strong> ${whitePlayer?.player_id || 'Waiting...'}
            </div>
            <div class="player-row">
                <strong>⚫ Black:</strong> ${blackPlayer?.player_id || 'Waiting...'}
            </div>
            <div class="player-row">
                <strong>Turn:</strong> ${state.position.turn.charAt(0).toUpperCase() + state.position.turn.slice(1)}
            </div>
        `;
    }
}
