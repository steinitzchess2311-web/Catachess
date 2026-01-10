/**
 * WebSocket Client Example
 *
 * Example implementation of a type-safe WebSocket client for CataChess.
 * This is a REFERENCE IMPLEMENTATION - adapt to your frontend framework.
 */

import type {
  ServerMessage,
  ClientMessage,
  GameState,
  MessageType,
  ProtocolErrorCode,
} from './types';
import { WS_BASE, WS_CONFIG } from './connection-config';

// ============================================================================
// Types for Client Usage
// ============================================================================

type MessageHandler = (message: ServerMessage) => void;
type ErrorHandler = (error: Error) => void;
type StateChangeHandler = (state: ConnectionState) => void;

type ConnectionState =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

interface GameClientOptions {
  gameId: string;
  playerId: string;
  onMessage?: MessageHandler;
  onError?: ErrorHandler;
  onStateChange?: StateChangeHandler;
  autoReconnect?: boolean;
}

// ============================================================================
// WebSocket Client Implementation
// ============================================================================

export class GameWebSocketClient {
  private ws: WebSocket | null = null;
  private seq = 0;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private state: ConnectionState = 'disconnected';

  // Options
  private gameId: string;
  private playerId: string;
  private onMessage?: MessageHandler;
  private onError?: ErrorHandler;
  private onStateChange?: StateChangeHandler;
  private autoReconnect: boolean;

  constructor(options: GameClientOptions) {
    this.gameId = options.gameId;
    this.playerId = options.playerId;
    this.onMessage = options.onMessage;
    this.onError = options.onError;
    this.onStateChange = options.onStateChange;
    this.autoReconnect = options.autoReconnect ?? true;
  }

  // ==========================================================================
  // Connection Management
  // ==========================================================================

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('Already connected');
      return;
    }

    this.setState('connecting');

    const url = `${WS_BASE}/game/${this.gameId}`;
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

  // ==========================================================================
  // Message Sending
  // ==========================================================================

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
      throw new Error('WebSocket not connected');
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
  }

  // ==========================================================================
  // Event Handlers
  // ==========================================================================

  private handleOpen(): void {
    console.log('WebSocket connected');
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

      // Handle message based on type
      switch (message.type) {
        case 'game_state':
          this.handleGameState(message);
          break;
        case 'error':
          this.handleProtocolError(message);
          break;
        case 'ack':
          this.handleAck(message);
          break;
        default:
          console.warn('Unknown message type:', message);
      }

      // Call user handler
      this.onMessage?.(message);
    } catch (error) {
      console.error('Failed to parse message:', error);
      this.onError?.(error as Error);
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.setState('error');
    this.onError?.(new Error('WebSocket error'));
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket closed:', event.code, event.reason);
    this.stopHeartbeat();

    if (this.autoReconnect && event.code !== 1000) {
      this.scheduleReconnect();
    } else {
      this.setState('disconnected');
    }
  }

  // ==========================================================================
  // Protocol Message Handlers
  // ==========================================================================

  private handleGameState(message: ServerMessage & { type: 'game_state' }): void {
    const state: GameState = message.payload;

    console.log('Game state update:', {
      state: state.state,
      turn: state.position.turn,
      moveNumber: state.position.move_number,
      result: state.position.result,
    });

    // You can add state management here (Redux, Zustand, etc.)
  }

  private handleProtocolError(message: ServerMessage & { type: 'error' }): void {
    const { code, message: errorMessage, details } = message.payload;

    console.error('Protocol error:', {
      code,
      message: errorMessage,
      details,
    });

    // Handle specific error codes
    switch (code as ProtocolErrorCode) {
      case 'INVALID_MOVE':
        console.error('Invalid move:', details);
        break;
      case 'NOT_YOUR_TURN':
        console.error('Not your turn');
        break;
      case 'GAME_NOT_FOUND':
        console.error('Game not found');
        this.disconnect();
        break;
      default:
        console.error('Unknown error code:', code);
    }
  }

  private handleAck(message: ServerMessage & { type: 'ack' }): void {
    const { ack_seq, status } = message.payload;
    console.log(`ACK received for seq ${ack_seq}:`, status);
  }

  // ==========================================================================
  // Reconnection Logic
  // ==========================================================================

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= WS_CONFIG.reconnect.maxAttempts) {
      console.error('Max reconnect attempts reached');
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

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  private stopReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ==========================================================================
  // Heartbeat Logic
  // ==========================================================================

  private startHeartbeat(): void {
    if (!WS_CONFIG.heartbeat.enabled) return;

    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Send ping (you can customize this)
        this.sync();
      }
    }, WS_CONFIG.heartbeat.interval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // ==========================================================================
  // State Management
  // ==========================================================================

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

// ============================================================================
// Usage Example
// ============================================================================

/**
 * Example: Create and use the client
 *
 * ```typescript
 * const client = new GameWebSocketClient({
 *   gameId: 'game_abc123',
 *   playerId: 'player_xyz789',
 *   onMessage: (msg) => {
 *     if (msg.type === 'game_state') {
 *       console.log('Game state:', msg.payload);
 *       // Update UI with msg.payload
 *     }
 *   },
 *   onError: (error) => {
 *     console.error('Error:', error);
 *   },
 *   onStateChange: (state) => {
 *     console.log('Connection state:', state);
 *   },
 * });
 *
 * // Connect
 * client.connect();
 *
 * // Make a move
 * client.move('e2e4');
 *
 * // Offer draw
 * client.offerDraw();
 *
 * // Disconnect
 * client.disconnect();
 * ```
 */

// ============================================================================
// React Hook Example
// ============================================================================

/**
 * Example: React hook for game client
 *
 * ```typescript
 * function useGameClient(gameId: string, playerId: string) {
 *   const [state, setState] = useState<GameState | null>(null);
 *   const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
 *   const clientRef = useRef<GameWebSocketClient | null>(null);
 *
 *   useEffect(() => {
 *     const client = new GameWebSocketClient({
 *       gameId,
 *       playerId,
 *       onMessage: (msg) => {
 *         if (msg.type === 'game_state') {
 *           setState(msg.payload);
 *         }
 *       },
 *       onStateChange: setConnectionState,
 *     });
 *
 *     client.connect();
 *     clientRef.current = client;
 *
 *     return () => {
 *       client.disconnect();
 *     };
 *   }, [gameId, playerId]);
 *
 *   const move = useCallback((move: string) => {
 *     clientRef.current?.move(move);
 *   }, []);
 *
 *   const resign = useCallback(() => {
 *     clientRef.current?.resign();
 *   }, []);
 *
 *   return {
 *     state,
 *     connectionState,
 *     move,
 *     resign,
 *     offerDraw: () => clientRef.current?.offerDraw(),
 *     acceptDraw: () => clientRef.current?.acceptDraw(),
 *     declineDraw: () => clientRef.current?.declineDraw(),
 *   };
 * }
 * ```
 */
