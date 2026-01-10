/**
 * Main UI Renderer - Coordinator for all region renderers
 */

import type { GameState } from '../core/types.js';
import type { ConnectionState } from '../core/ws.js';
import { InfoRenderer } from '../renderers/info.js';
import { ClockRenderer } from '../renderers/clock.js';
import { HistoryRenderer } from '../renderers/history.js';
import { BoardRenderer } from '../renderers/board.js';
import { ChatRenderer } from '../renderers/chat.js';
import { ActionsRenderer } from '../renderers/actions.js';

export class UIRenderer {
    private info: InfoRenderer;
    private clock: ClockRenderer;
    private history: HistoryRenderer;
    private board: BoardRenderer;
    private chat: ChatRenderer;
    private actions: ActionsRenderer;

    constructor() {
        this.info = new InfoRenderer();
        this.clock = new ClockRenderer();
        this.history = new HistoryRenderer();
        this.board = new BoardRenderer();
        this.chat = new ChatRenderer();
        this.actions = new ActionsRenderer();
    }

    render(state: GameState | null): void {
        if (!state) {
            this.board.renderEmpty();
            return;
        }

        this.info.render(state);
        this.clock.render(state);
        this.history.render(state);
        this.board.render(state);
        this.actions.render(state);
    }

    renderConnectionState(state: ConnectionState): void {
        console.log('[Renderer] Connection state:', state);

        const root = document.getElementById('games-root');
        if (root) {
            root.dataset.connectionState = state;
        }
    }

    addChatMessage(message: string, sender?: string): void {
        this.chat.addMessage(message, sender);
    }

    clearChat(): void {
        this.chat.clear();
    }
}
