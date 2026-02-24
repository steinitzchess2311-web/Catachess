// ============================================================
// user_games — 类型定义
// Base URL: https://gameserver.catachess.com
// ============================================================

// ---- 时间控制 ------------------------------------------------

export interface TimeControl {
  initial: number;   // 初始时间（秒）
  increment: number; // 每步加秒
}

// ---- 对局状态 ------------------------------------------------

export type GameStatus = 'open' | 'waiting' | 'ongoing' | 'completed' | 'aborted';

export type PlayerColor = 'white' | 'black';

// 对局结束原因
export type GameEndReason =
  | 'checkmate'
  | 'resignation'
  | 'timeout'
  | 'stalemate'
  | 'draw_agreement'
  | 'insufficient_material'
  | 'fifty_moves'
  | 'threefold_repetition'
  | 'aborted';

// ---- HTTP 响应类型 ------------------------------------------

/** POST /api/game/create-open 的响应 */
export interface CreateOpenGameResponse {
  game_id: string;
  status: 'open';
  created_by: string;
}

/** POST /api/game/{game_id}/join 的响应 */
export interface JoinGameResponse {
  game_id: string;
  white_player_id: string;
  black_player_id: string;
  /** 仅匿名加入时有值，前端必须持久化用于 WS 连接 */
  anon_user_id: string | null;
}

/** POST /api/game/create 的响应 */
export interface CreateGameResponse {
  game_id: string;
  white_player_id: string;
  black_player_id: string;
  time_control: TimeControl;
  status: GameStatus;
  created_at: string;
}

/** GET /api/game/current 的响应（null 表示无进行中对局）*/
export interface CurrentGameResponse {
  game_id: string;
  white_player_id: string;
  black_player_id: string;
  your_color: PlayerColor;
  opponent: { id: string };
  status: GameStatus;
  time_control: TimeControl;
  current_state: {
    fen: string;
    turn: PlayerColor;
    move_count: number;
    is_check: boolean;
  };
  created_at: string;
}

/** GET /api/game/{game_id} 的响应 */
export interface GameDetail {
  game_id: string;
  white_player_id: string;
  /** open 状态时为 null */
  black_player_id: string | null;
  /** 创建者 ID（open 对局时有意义）*/
  created_by?: string;
  status: GameStatus;
  result: string | null;   // '1-0' | '0-1' | '1/2-1/2'
  end_reason: GameEndReason | null;
  time_control: TimeControl;
  moves: string[];         // SAN 走法数组
  final_fen: string | null;
  created_at: string;
  ended_at: string | null;
}

/** GET /api/game/list 中单条记录 */
export interface GameHistoryItem {
  game_id: string;
  opponent_id: string;
  your_color: PlayerColor;
  result: string | null;
  end_reason: GameEndReason | null;
  status: GameStatus;
  move_count: number;
  time_control: TimeControl;
  created_at: string;
  ended_at: string | null;
}

/** GET /api/game/list 的响应 */
export interface GameListResponse {
  games: GameHistoryItem[];
  next_cursor: string | null;
  has_more: boolean;
}

// ---- WebSocket 消息类型 -------------------------------------

/** 时钟状态（秒，浮点数）*/
export interface ClockState {
  white: number;
  black: number;
}

/** 走棋详情 */
export interface MoveDetail {
  san: string;
  uci: string;
  from: string;
  to: string;
  captured: string | null;
  promotion: string | null;
  is_check: boolean;
  is_checkmate: boolean;
}

// 服务器推送消息 —— 严格 discriminated union

export type ServerMessage =
  | {
      type: 'game_state';
      game_id: string;
      white_player_id: string;
      black_player_id: string;
      your_color: PlayerColor;
      status: GameStatus;
      fen: string;
      turn: PlayerColor;
      move_count: number;
      time_remaining: ClockState;
    }
  | {
      type: 'move_made';
      move: MoveDetail;
      fen: string;
      turn: PlayerColor;
      time_remaining: ClockState;
      is_check: boolean;
      is_checkmate: boolean;
    }
  | {
      type: 'time_update';
      time_remaining: ClockState;
    }
  | {
      type: 'game_over';
      result: string;
      reason: GameEndReason;
      winner: PlayerColor | null;
    }
  | {
      type: 'draw_offered';
      from_player: string;
    }
  | { type: 'opponent_disconnected' }
  | { type: 'opponent_reconnected' }
  | {
      type: 'error';
      error: string;
      message: string;
    }
  | { type: 'pong' };

// 客户端发送消息

export type ClientMessage =
  | { type: 'move'; from: string; to: string; promotion?: string }
  | { type: 'resign' }
  | { type: 'offer_draw' }
  | { type: 'accept_draw' }
  | { type: 'decline_draw' }
  | { type: 'ping' };

// ---- WebSocket hook 对外暴露的状态 --------------------------

export type GamePhase = 'connecting' | 'waiting' | 'ongoing' | 'over' | 'disconnected';

export interface DrawOfferState {
  incoming: boolean;   // 对手提和，等我响应
  outgoing: boolean;   // 我提和，等对手响应
}

export interface GameResult {
  result: string;
  reason: GameEndReason;
  winner: PlayerColor | null;
}

export interface LiveGameState {
  phase: GamePhase;
  fen: string;
  turn: PlayerColor;
  myColor: PlayerColor | null;
  whiteId: string;
  blackId: string;
  clockWhite: number;   // 毫秒
  clockBlack: number;
  moves: string[];      // SAN 列表，用于走法列表显示
  drawOffer: DrawOfferState;
  result: GameResult | null;
  opponentDisconnected: boolean;
  error: string | null;
}
