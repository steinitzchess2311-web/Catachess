/**
 * WebSocket Protocol Types
 *
 * TypeScript mirror of server protocol types.
 * Source: game_server/ws_protocol/protocol_core/types.py
 *
 * ⚠️ This is a READ-ONLY mirror - server is the source of truth.
 * Do NOT modify these types without updating the server first.
 */

// ============================================================================
// Message Types (Enum)
// ============================================================================

/**
 * Supported WebSocket message types
 * Maps to server's MessageType enum
 */
export type MessageType =
  // Client → Server
  | "join"
  | "reconnect"
  | "move"
  | "resign"
  | "draw_offer"
  | "draw_accept"
  | "draw_decline"
  | "sync"
  // Server → Client
  | "game_state"
  | "error"
  | "ack";

// ============================================================================
// Base Message Structure
// ============================================================================

/**
 * Base structure for all WebSocket messages
 * Maps to server's ParsedMessage dataclass
 */
export interface BaseMessage {
  type: MessageType;
  game_id: string;
  player_id: string;
  seq: number;
  payload: Record<string, any>;
  timestamp?: number;
}

// ============================================================================
// Client → Server Messages
// ============================================================================

/**
 * JOIN: Player joins a game
 */
export interface JoinMessage extends BaseMessage {
  type: "join";
  payload: {
    // Add specific join payload fields if needed
  };
}

/**
 * RECONNECT: Player reconnects with existing player_id
 */
export interface ReconnectMessage extends BaseMessage {
  type: "reconnect";
  payload: {
    // Add specific reconnect payload fields if needed
  };
}

/**
 * MOVE: Player makes a move
 */
export interface MoveMessage extends BaseMessage {
  type: "move";
  payload: {
    move: string; // e.g., "e2e4", chess notation
    // Add other move-related fields if needed
  };
}

/**
 * RESIGN: Player resigns
 */
export interface ResignMessage extends BaseMessage {
  type: "resign";
  payload: Record<string, never>; // Empty payload
}

/**
 * DRAW_OFFER: Player offers a draw
 */
export interface DrawOfferMessage extends BaseMessage {
  type: "draw_offer";
  payload: Record<string, never>; // Empty payload
}

/**
 * DRAW_ACCEPT: Player accepts draw offer
 */
export interface DrawAcceptMessage extends BaseMessage {
  type: "draw_accept";
  payload: Record<string, never>; // Empty payload
}

/**
 * DRAW_DECLINE: Player declines draw offer
 */
export interface DrawDeclineMessage extends BaseMessage {
  type: "draw_decline";
  payload: Record<string, never>; // Empty payload
}

/**
 * SYNC: Request full game state sync
 */
export interface SyncMessage extends BaseMessage {
  type: "sync";
  payload: Record<string, never>; // Empty payload
}

// ============================================================================
// Server → Client Messages
// ============================================================================

/**
 * GAME_STATE: Complete game state update
 * Payload structure matches export_state() from server
 */
export interface GameStateMessage extends BaseMessage {
  type: "game_state";
  payload: GameState;
}

/**
 * ERROR: Server error response
 */
export interface ErrorMessage extends BaseMessage {
  type: "error";
  payload: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}

/**
 * ACK: Acknowledgment of received message
 */
export interface AckMessage extends BaseMessage {
  type: "ack";
  payload: {
    ack_seq: number; // Sequence number being acknowledged
    status?: string;
  };
}

// ============================================================================
// Union Types
// ============================================================================

/**
 * All possible client messages
 */
export type ClientMessage =
  | JoinMessage
  | ReconnectMessage
  | MoveMessage
  | ResignMessage
  | DrawOfferMessage
  | DrawAcceptMessage
  | DrawDeclineMessage
  | SyncMessage;

/**
 * All possible server messages
 */
export type ServerMessage =
  | GameStateMessage
  | ErrorMessage
  | AckMessage;

/**
 * Any WebSocket message
 */
export type WSMessage = ClientMessage | ServerMessage;

// ============================================================================
// Game State Structure
// ============================================================================

/**
 * Complete game state
 * Matches export_state() return value from server
 * Source: game_server/game/game_core/export.py::export_state()
 */
export interface GameState {
  game_id: string;
  state: GameStateValue;
  created_at: number;

  /**
   * Player information
   * Key: player_id, Value: player details
   */
  players: Record<string, PlayerInfo>;

  /**
   * Current position state
   */
  position: PositionState;

  /**
   * Clock remaining time (if clock is enabled)
   * Key: color ("white" | "black"), Value: seconds remaining
   */
  clock?: Record<string, number>;

  /**
   * End information (only present if game is ended)
   */
  ended_at?: number;
  end_reason?: string;
}

/**
 * Game state values
 */
export type GameStateValue =
  | "waiting"
  | "active"
  | "ended";

/**
 * Player information
 */
export interface PlayerInfo {
  color: "white" | "black";
  player_id: string;
}

/**
 * Chess position state
 */
export interface PositionState {
  turn: "white" | "black";
  move_number: number;
  move_history: string[]; // Array of moves in algebraic notation
  fen: string; // FEN notation
  result: GameResult;
}

/**
 * Game result values
 */
export type GameResult =
  | "in_progress"
  | "white_wins"
  | "black_wins"
  | "draw"
  | "aborted";

// ============================================================================
// Protocol Error
// ============================================================================

/**
 * Protocol error codes
 */
export type ProtocolErrorCode =
  | "PROTOCOL_ERROR"
  | "INVALID_MESSAGE"
  | "UNAUTHORIZED"
  | "GAME_NOT_FOUND"
  | "INVALID_MOVE"
  | "NOT_YOUR_TURN"
  | "GAME_ENDED";

/**
 * Protocol error structure
 */
export interface ProtocolError {
  code: ProtocolErrorCode;
  message: string;
}
