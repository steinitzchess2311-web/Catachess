/**
 * Event Handlers - UI Events → Actions
 * Handles user interactions and triggers appropriate actions
 */

import type { GameWSClient } from '../core/ws.js';

// ============================================================================
// Event Manager
// ============================================================================

export class EventManager {
    private wsClient: GameWSClient | null = null;

    /**
     * Set the WebSocket client to use for sending actions
     */
    setWSClient(client: GameWSClient): void {
        this.wsClient = client;
    }

    /**
     * Initialize all event listeners
     */
    init(): void {
        this.initActionButtons();
        this.initBoardEvents();
        this.initChatEvents();
    }

    // ========================================================================
    // Action Button Events
    // ========================================================================

    private initActionButtons(): void {
        const resignBtn = document.getElementById('action-resign');
        const drawBtn = document.getElementById('action-draw');
        const takebackBtn = document.getElementById('action-takeback');
        const extraBtn = document.getElementById('action-extra');

        resignBtn?.addEventListener('click', () => this.handleResign());
        drawBtn?.addEventListener('click', () => this.handleDrawOffer());
        takebackBtn?.addEventListener('click', () => this.handleTakeback());
        extraBtn?.addEventListener('click', () => this.handleExtra());
    }

    private handleResign(): void {
        if (!this.wsClient?.isConnected()) {
            console.warn('[Events] Cannot resign - not connected');
            return;
        }

        const confirmed = confirm('Are you sure you want to resign?');
        if (confirmed) {
            console.log('[Events] Resigning');
            this.wsClient.resign();
        }
    }

    private handleDrawOffer(): void {
        if (!this.wsClient?.isConnected()) {
            console.warn('[Events] Cannot offer draw - not connected');
            return;
        }

        console.log('[Events] Offering draw');
        this.wsClient.offerDraw();
    }

    private handleTakeback(): void {
        console.log('[Events] Takeback requested (not yet implemented)');
        // TODO: Implement takeback logic
    }

    private handleExtra(): void {
        console.log('[Events] Extra action clicked');
        // TODO: Implement extra menu (settings, export PGN, etc.)
    }

    // ========================================================================
    // Board Events
    // ========================================================================

    private initBoardEvents(): void {
        const board = document.getElementById('chess-board');

        board?.addEventListener('click', (event) => {
            this.handleBoardClick(event);
        });
    }

    private handleBoardClick(event: MouseEvent): void {
        // Placeholder: Will be implemented with actual board rendering
        console.log('[Events] Board clicked at:', event.offsetX, event.offsetY);

        // TODO: Implement square selection and move making
        // Example flow:
        // 1. Detect which square was clicked
        // 2. If no piece selected, select piece
        // 3. If piece selected, attempt move
        // 4. Send move via wsClient.move('e2e4')
    }

    // ========================================================================
    // Chat Events
    // ========================================================================

    private initChatEvents(): void {
        const chatInputArea = document.getElementById('chat-input-area');

        // Placeholder: Will be implemented when chat input is added
        chatInputArea?.addEventListener('click', () => {
            console.log('[Events] Chat input clicked (placeholder)');
        });
    }

    // ========================================================================
    // Keyboard Events
    // ========================================================================

    /**
     * Initialize global keyboard shortcuts
     */
    initKeyboard(): void {
        document.addEventListener('keydown', (event) => {
            // Handle keyboard shortcuts
            if (event.ctrlKey || event.metaKey) {
                switch (event.key.toLowerCase()) {
                    case 'z':
                        // Undo last move
                        event.preventDefault();
                        this.handleTakeback();
                        break;
                }
            }

            // Escape key to deselect
            if (event.key === 'Escape') {
                // TODO: Deselect selected piece
                console.log('[Events] Escape pressed');
            }
        });
    }

    // ========================================================================
    // Utility Methods
    // ========================================================================

    /**
     * Clean up all event listeners
     */
    destroy(): void {
        // Remove listeners if needed for cleanup
        console.log('[Events] Cleaning up event listeners');
    }
}
