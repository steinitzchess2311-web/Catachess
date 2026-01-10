/**
 * Server Connection Configuration
 *
 * Connection details for frontend → server communication.
 * These are constants based on your deployment setup.
 */

// ============================================================================
// Server Endpoints
// ============================================================================

/**
 * Base URL for HTTP/HTTPS API requests
 */
export const API_BASE = "https://iloveliquanhao.catachess.com";

/**
 * Base URL for WebSocket connections
 */
export const WS_BASE = "wss://iloveliquanhao.catachess.com/ws";

// ============================================================================
// Environment-based Configuration (Optional)
// ============================================================================

/**
 * Get API base URL (supports environment override)
 */
export function getApiBase(): string {
  if (typeof process !== "undefined" && process.env?.VITE_API_BASE) {
    return process.env.VITE_API_BASE;
  }
  return API_BASE;
}

/**
 * Get WebSocket base URL (supports environment override)
 */
export function getWsBase(): string {
  if (typeof process !== "undefined" && process.env?.VITE_WS_BASE) {
    return process.env.VITE_WS_BASE;
  }
  return WS_BASE;
}

// ============================================================================
// Connection Settings
// ============================================================================

/**
 * WebSocket connection configuration
 */
export const WS_CONFIG = {
  /**
   * Reconnection settings
   */
  reconnect: {
    enabled: true,
    maxAttempts: 5,
    initialDelay: 1000, // ms
    maxDelay: 30000, // ms
    backoffMultiplier: 2,
  },

  /**
   * Heartbeat/ping settings
   */
  heartbeat: {
    enabled: true,
    interval: 30000, // ms - send ping every 30s
    timeout: 5000, // ms - wait 5s for pong
  },

  /**
   * Message settings
   */
  message: {
    maxRetries: 3,
    ackTimeout: 5000, // ms - wait for ACK
  },
};

// ============================================================================
// Usage Examples
// ============================================================================

/**
 * Example: Create WebSocket connection
 *
 * ```typescript
 * const ws = new WebSocket(`${WS_BASE}/game/${gameId}`);
 * ```
 */

/**
 * Example: Make HTTP request
 *
 * ```typescript
 * const response = await fetch(`${API_BASE}/api/games/${gameId}`);
 * ```
 */
