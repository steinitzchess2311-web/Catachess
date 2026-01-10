/**
 * Actions Renderer - Action button states
 */

import type { GameState } from '../core/types.js';

export class ActionsRenderer {
    private actionResign: HTMLElement;
    private actionDraw: HTMLElement;
    private actionTakeback: HTMLElement;
    private actionExtra: HTMLElement;

    constructor() {
        this.actionResign = document.getElementById('action-resign')!;
        this.actionDraw = document.getElementById('action-draw')!;
        this.actionTakeback = document.getElementById('action-takeback')!;
        this.actionExtra = document.getElementById('action-extra')!;
    }

    render(state: GameState): void {
        // Enable/disable buttons based on game state
        if (state.state === 'ended') {
            this.actionResign.style.opacity = '0.5';
            this.actionResign.style.pointerEvents = 'none';
            this.actionDraw.style.opacity = '0.5';
            this.actionDraw.style.pointerEvents = 'none';
        } else {
            this.actionResign.style.opacity = '1';
            this.actionResign.style.pointerEvents = 'auto';
            this.actionDraw.style.opacity = '1';
            this.actionDraw.style.pointerEvents = 'auto';
        }
    }
}
