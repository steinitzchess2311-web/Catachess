/**
 * Clock Renderer - Chess clock display
 */

import type { GameState } from '../core/types.js';

export class ClockRenderer {
    private clockWhite: HTMLElement;
    private clockBlack: HTMLElement;

    constructor() {
        this.clockWhite = document.getElementById('clock-white')!;
        this.clockBlack = document.getElementById('clock-black')!;
    }

    render(state: GameState): void {
        if (state.clock) {
            this.clockWhite.textContent = this.formatTime(state.clock.white || 0);
            this.clockBlack.textContent = this.formatTime(state.clock.black || 0);

            // Highlight active clock
            if (state.position.turn === 'white') {
                this.clockWhite.classList.add('active');
                this.clockBlack.classList.remove('active');
            } else {
                this.clockBlack.classList.add('active');
                this.clockWhite.classList.remove('active');
            }
        } else {
            this.clockWhite.textContent = '∞';
            this.clockBlack.textContent = '∞';
            this.clockWhite.classList.remove('active');
            this.clockBlack.classList.remove('active');
        }
    }

    private formatTime(seconds: number): string {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}
