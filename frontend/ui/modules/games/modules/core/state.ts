/**
 * State Management - Simple Observable State
 * Stores current game state and notifies subscribers of changes
 */

import type { GameState } from './types.js';
import type { ConnectionState } from './ws.js';

// ============================================================================
// Types
// ============================================================================

export type StateChangeHandler = (state: GameState | null) => void;
export type ConnectionStateHandler = (state: ConnectionState) => void;

// ============================================================================
// Game State Manager
// ============================================================================

export class GameStateManager {
    private gameState: GameState | null = null;
    private connectionState: ConnectionState = 'disconnected';
    private stateSubscribers: Set<StateChangeHandler> = new Set();
    private connectionSubscribers: Set<ConnectionStateHandler> = new Set();

    // ========================================================================
    // Game State
    // ========================================================================

    /**
     * Update game state and notify subscribers
     */
    updateGameState(state: GameState): void {
        this.gameState = state;
        console.log('[State] Game state updated:', state.state, 'move:', state.position.move_number);
        this.notifyStateSubscribers();
    }

    /**
     * Get current game state
     */
    getGameState(): GameState | null {
        return this.gameState;
    }

    /**
     * Clear game state
     */
    clearGameState(): void {
        this.gameState = null;
        this.notifyStateSubscribers();
    }

    // ========================================================================
    // Connection State
    // ========================================================================

    /**
     * Update connection state and notify subscribers
     */
    updateConnectionState(state: ConnectionState): void {
        this.connectionState = state;
        console.log('[State] Connection state:', state);
        this.notifyConnectionSubscribers();
    }

    /**
     * Get current connection state
     */
    getConnectionState(): ConnectionState {
        return this.connectionState;
    }

    // ========================================================================
    // Subscriptions
    // ========================================================================

    /**
     * Subscribe to game state changes
     */
    subscribeToGameState(handler: StateChangeHandler): () => void {
        this.stateSubscribers.add(handler);

        // Immediately call with current state
        handler(this.gameState);

        // Return unsubscribe function
        return () => {
            this.stateSubscribers.delete(handler);
        };
    }

    /**
     * Subscribe to connection state changes
     */
    subscribeToConnectionState(handler: ConnectionStateHandler): () => void {
        this.connectionSubscribers.add(handler);

        // Immediately call with current state
        handler(this.connectionState);

        // Return unsubscribe function
        return () => {
            this.connectionSubscribers.delete(handler);
        };
    }

    // ========================================================================
    // Private Methods
    // ========================================================================

    private notifyStateSubscribers(): void {
        for (const handler of this.stateSubscribers) {
            handler(this.gameState);
        }
    }

    private notifyConnectionSubscribers(): void {
        for (const handler of this.connectionSubscribers) {
            handler(this.connectionState);
        }
    }
}

// ============================================================================
// Singleton Instance
// ============================================================================

export const gameStateManager = new GameStateManager();
