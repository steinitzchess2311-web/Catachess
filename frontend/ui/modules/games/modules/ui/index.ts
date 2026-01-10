/**
 * CataChess Game Module - Main Entry Point
 * Initializes and coordinates all game components
 */

import { GameWSClient } from '../core/ws.js';
import { gameStateManager } from '../core/state.js';
import { UIRenderer } from './renderer.js';
import { EventManager } from './events.js';
import type { ServerMessage } from '../core/types.js';

// ============================================================================
// Main Application Controller
// ============================================================================

class GameApp {
    private wsClient: GameWSClient | null = null;
    private renderer: UIRenderer;
    private eventManager: EventManager;

    constructor() {
        this.renderer = new UIRenderer();
        this.eventManager = new EventManager();
    }

    /**
     * Initialize and connect to a game
     */
    init(gameId: string, playerId: string): void {
        console.log('[GameApp] Initializing...', { gameId, playerId });

        // Create WebSocket client
        this.wsClient = new GameWSClient({
            gameId,
            playerId,
            onMessage: (msg) => this.handleMessage(msg),
            onStateChange: (state) => this.handleConnectionState(state),
            onError: (error) => this.handleError(error),
            autoReconnect: true,
        });

        // Set up event manager
        this.eventManager.setWSClient(this.wsClient);
        this.eventManager.init();
        this.eventManager.initKeyboard();

        // Subscribe to state changes
        gameStateManager.subscribeToGameState((state) => {
            this.renderer.render(state);
        });

        gameStateManager.subscribeToConnectionState((state) => {
            this.renderer.renderConnectionState(state);
        });

        // Connect to server
        this.wsClient.connect();

        console.log('[GameApp] Initialized successfully');
    }

    /**
     * Handle incoming WebSocket messages
     */
    private handleMessage(message: ServerMessage): void {
        switch (message.type) {
            case 'game_state':
                gameStateManager.updateGameState(message.payload);
                break;

            case 'error':
                console.error('[GameApp] Server error:', message.payload);
                this.renderer.addChatMessage(
                    `Error: ${message.payload.message}`,
                    'System'
                );
                break;

            case 'ack':
                console.log('[GameApp] ACK received:', message.payload);
                break;

            default:
                console.warn('[GameApp] Unknown message type:', message);
        }
    }

    /**
     * Handle connection state changes
     */
    private handleConnectionState(state: string): void {
        gameStateManager.updateConnectionState(state as any);
    }

    /**
     * Handle errors
     */
    private handleError(error: Error): void {
        console.error('[GameApp] Error:', error);
        this.renderer.addChatMessage(`Error: ${error.message}`, 'System');
    }

    /**
     * Clean up and disconnect
     */
    destroy(): void {
        this.wsClient?.disconnect();
        this.eventManager.destroy();
        console.log('[GameApp] Destroyed');
    }
}

// ============================================================================
// Auto-initialization
// ============================================================================

// Extract game ID and player ID from URL
const urlParams = new URLSearchParams(window.location.search);
const gameId = urlParams.get('gameId') || 'test-game';
const playerId = urlParams.get('playerId') || 'test-player';

// Wait for DOM to load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const app = new GameApp();
        app.init(gameId, playerId);
        (window as any).gameApp = app; // Expose for debugging
    });
} else {
    const app = new GameApp();
    app.init(gameId, playerId);
    (window as any).gameApp = app; // Expose for debugging
}
