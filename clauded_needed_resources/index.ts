/**
 * CataChess Protocol - Main Export
 *
 * Single entry point for all protocol types and utilities.
 */

// ============================================================================
// Type Definitions
// ============================================================================

export type {
  // Message Types
  MessageType,
  BaseMessage,
  ClientMessage,
  ServerMessage,
  WSMessage,

  // Client → Server Messages
  JoinMessage,
  ReconnectMessage,
  MoveMessage,
  ResignMessage,
  DrawOfferMessage,
  DrawAcceptMessage,
  DrawDeclineMessage,
  SyncMessage,

  // Server → Client Messages
  GameStateMessage,
  ErrorMessage,
  AckMessage,

  // Game State
  GameState,
  GameStateValue,
  PlayerInfo,
  PositionState,
  GameResult,

  // Errors
  ProtocolError,
  ProtocolErrorCode,
} from './types';

// ============================================================================
// Connection Configuration
// ============================================================================

export {
  API_BASE,
  WS_BASE,
  WS_CONFIG,
  getApiBase,
  getWsBase,
} from './connection-config';

// ============================================================================
// WebSocket Client (Optional)
// ============================================================================

// Uncomment if you want to use the example client
// export { GameWebSocketClient } from './websocket-client-example';

// ============================================================================
// Usage
// ============================================================================

/**
 * Basic usage:
 *
 * ```typescript
 * import type { GameState, ServerMessage } from './index';
 * import { WS_BASE } from './index';
 *
 * const ws = new WebSocket(`${WS_BASE}/game/${gameId}`);
 *
 * ws.onmessage = (event) => {
 *   const msg: ServerMessage = JSON.parse(event.data);
 *   if (msg.type === 'game_state') {
 *     const state: GameState = msg.payload;
 *     // Use state
 *   }
 * };
 * ```
 */
