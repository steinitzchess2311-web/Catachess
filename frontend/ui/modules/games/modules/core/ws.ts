/**
 * WebSocket Client - Professional Implementation
 * Handles connection, reconnection, and message sending/receiving
 */

import type {
    ServerMessage,
    ClientMessage,
    MessageType,
} from './types.js';
import { WS_BASE, WS_CONFIG } from './config.js';

// ============================================================================
// Types
// ============================================================================

export type ConnectionState =
    | 'disconnected'
    | 'connecting'
    | 'connected'
    | 'reconnecting'
    | 'error';

export type MessageHandler = (message: ServerMessage) => void;
export type StateChangeHandler = (state: ConnectionState) => void;
export type ErrorHandler = (error: Error) => void;

export interface WSClientOptions {
    gameId: string;
    playerId: string;
    onMessage?: MessageHandler;
    onStateChange?: StateChangeHandler;
    onError?: ErrorHandler;
    autoReconnect?: boolean;
}

// ============================================================================
// WebSocket Client
// ============================================================================

export class GameWSClient {
    private ws: WebSocket | null = null;
    private seq = 0;
    private reconnectAttempts = 0;
    private reconnectTimer: number | null = null;
    private heartbeatTimer: number | null = null;
    private state: ConnectionState = 'disconnected';

    // Options
    private gameId: string;
    private playerId: string;
    private onMessage?: MessageHandler;
    private onStateChange?: StateChangeHandler;
    private onError?: ErrorHandler;
    private autoReconnect: boolean;

    constructor(options: WSClientOptions) {
        this.gameId = options.gameId;
        this.playerId = options.playerId;
        this.onMessage = options.onMessage;
        this.onStateChange = options.onStateChange;
        this.onError = options.onError;
        this.autoReconnect = options.autoReconnect ?? true;
    }

    // ========================================================================
    // Connection Management
    // ========================================================================

    connect(): void {
        if (this.ws?.readyState === WebSocket.OPEN) {
            console.warn('[WS] Already connected');
            return;
        }

        this.setState('connecting');

        const url = `${WS_BASE}/game/${this.gameId}`;
        console.log('[WS] Connecting to:', url);

        this.ws = new WebSocket(url);

        this.ws.onopen = () => this.handleOpen();
        this.ws.onmessage = (event) => this.handleMessage(event);
        this.ws.onerror = (event) => this.handleError(event);
        this.ws.onclose = (event) => this.handleClose(event);
    }

    disconnect(): void {
        this.autoReconnect = false;
        this.stopReconnectTimer();
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.setState('disconnected');
    }

    // ========================================================================
    // Message Sending
    // ========================================================================

    /**
     * Send JOIN message
     */
    join(): void {
        this.send('join', {});
    }

    /**
     * Send RECONNECT message
     */
    reconnect(): void {
        this.send('reconnect', {});
    }

    /**
     * Send MOVE message
     */
    move(move: string): void {
        this.send('move', { move });
    }

    /**
     * Send RESIGN message
     */
    resign(): void {
        this.send('resign', {});
    }

    /**
     * Send DRAW_OFFER message
     */
    offerDraw(): void {
        this.send('draw_offer', {});
    }

    /**
     * Send DRAW_ACCEPT message
     */
    acceptDraw(): void {
        this.send('draw_accept', {});
    }

    /**
     * Send DRAW_DECLINE message
     */
    declineDraw(): void {
        this.send('draw_decline', {});
    }

    /**
     * Request full state sync
     */
    sync(): void {
        this.send('sync', {});
    }

    /**
     * Generic send method
     */
    private send(type: MessageType, payload: Record<string, any>): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('[WS] Cannot send - not connected');
            return;
        }

        const message: ClientMessage = {
            type: type as any,
            game_id: this.gameId,
            player_id: this.playerId,
            seq: ++this.seq,
            payload,
            timestamp: Date.now() / 1000,
        };

        this.ws.send(JSON.stringify(message));
        console.log('[WS] Sent:', message.type, 'seq:', message.seq);
    }

    // ========================================================================
    // Event Handlers
    // ========================================================================

    private handleOpen(): void {
        console.log('[WS] Connected');
        this.setState('connected');
        this.reconnectAttempts = 0;
        this.startHeartbeat();

        // Auto-join or reconnect
        if (this.seq === 0) {
            this.join();
        } else {
            this.reconnect();
        }
    }

    private handleMessage(event: MessageEvent): void {
        try {
            const message: ServerMessage = JSON.parse(event.data);

            console.log('[WS] Received:', message.type, 'seq:', message.seq);

            // Call user handler
            this.onMessage?.(message);
        } catch (error) {
            console.error('[WS] Failed to parse message:', error);
            this.onError?.(error as Error);
        }
    }

    private handleError(event: Event): void {
        console.error('[WS] Error:', event);
        this.setState('error');
        this.onError?.(new Error('WebSocket error'));
    }

    private handleClose(event: CloseEvent): void {
        console.log('[WS] Closed:', event.code, event.reason);
        this.stopHeartbeat();

        if (this.autoReconnect && event.code !== 1000) {
            this.scheduleReconnect();
        } else {
            this.setState('disconnected');
        }
    }

    // ========================================================================
    // Reconnection Logic
    // ========================================================================

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= WS_CONFIG.reconnect.maxAttempts) {
            console.error('[WS] Max reconnect attempts reached');
            this.setState('error');
            this.onError?.(new Error('Max reconnect attempts reached'));
            return;
        }

        this.setState('reconnecting');

        const delay = Math.min(
            WS_CONFIG.reconnect.initialDelay *
                Math.pow(WS_CONFIG.reconnect.backoffMultiplier, this.reconnectAttempts),
            WS_CONFIG.reconnect.maxDelay
        );

        console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

        this.reconnectTimer = window.setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
        }, delay);
    }

    private stopReconnectTimer(): void {
        if (this.reconnectTimer !== null) {
            window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    // ========================================================================
    // Heartbeat Logic
    // ========================================================================

    private startHeartbeat(): void {
        if (!WS_CONFIG.heartbeat.enabled) return;

        this.heartbeatTimer = window.setInterval(() => {
            if (this.ws?.readyState === WebSocket.OPEN) {
                this.sync();
            }
        }, WS_CONFIG.heartbeat.interval);
    }

    private stopHeartbeat(): void {
        if (this.heartbeatTimer !== null) {
            window.clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    // ========================================================================
    // State Management
    // ========================================================================

    private setState(state: ConnectionState): void {
        this.state = state;
        this.onStateChange?.(state);
    }

    getState(): ConnectionState {
        return this.state;
    }

    isConnected(): boolean {
        return this.state === 'connected';
    }
}
