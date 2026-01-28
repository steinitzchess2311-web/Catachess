/**
 * CataMaze command handlers
 */
import { apiClient, Observation } from '../apiClient';
import type { CommandResult } from '@patch/modules/terminal/types';
import {
  renderGameState,
  renderEventLog,
  renderGameOver,
  renderHelp,
} from '../renderer';

interface GameState {
  gameId: string | null;
  observation: Observation | null;
  queueSize: number;
}

export const keyToAction: Record<string, string> = {
  w: 'MOVE_UP',
  a: 'MOVE_LEFT',
  s: 'MOVE_DOWN',
  d: 'MOVE_RIGHT',
  up: 'MOVE_UP',
  left: 'MOVE_LEFT',
  down: 'MOVE_DOWN',
  right: 'MOVE_RIGHT',
  i: 'SHOOT_UP',
  j: 'SHOOT_LEFT',
  k: 'SHOOT_DOWN',
  l: 'SHOOT_RIGHT',
  space: 'WAIT',
  '.': 'WAIT',
};

export async function handleNew(gameStateRef: { current: GameState }): Promise<CommandResult> {
  try {
    const response = await apiClient.createGame();
    gameStateRef.current = {
      gameId: response.game_id,
      observation: response.observation,
      queueSize: response.queue_size,
    };
    return {
      output: [
        '=== NEW GAME STARTED ===',
        `Game ID: ${response.game_id}`,
        '',
        ...renderGameState(response.observation),
        '',
        'Type "catamaze action <keys>" to queue actions, "catamaze tick" to execute.',
      ],
    };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleAction(
  gameStateRef: { current: GameState },
  key: string | undefined
): Promise<CommandResult> {
  if (!gameStateRef.current.gameId) {
    return { output: ['No active game. Use "catamaze new" to start.'], error: true };
  }
  if (!key) {
    return { output: ['Usage: catamaze action <key>', 'Keys: w/a/s/d, i/j/k/l, space'], error: true };
  }
  const keys = key.split('');
  const actions: string[] = [];
  const invalidKeys: string[] = [];
  for (const k of keys) {
    const action = keyToAction[k.toLowerCase()];
    if (action) {
      actions.push(action);
    } else if (k !== ' ') {
      invalidKeys.push(k);
    }
  }
  if (invalidKeys.length > 0) {
    return { output: [`Invalid keys: ${invalidKeys.join(', ')}`, 'Valid keys: w/a/s/d, i/j/k/l, space'], error: true };
  }
  if (actions.length === 0) {
    return { output: ['No valid actions provided'], error: true };
  }
  try {
    for (const action of actions) {
      const response = await apiClient.submitAction(gameStateRef.current.gameId, action);
      gameStateRef.current.queueSize = response.queue_size;
    }
    return {
      output: [
        `${actions.length} action(s) queued`,
        `Queue size: ${gameStateRef.current.queueSize}`,
        'Use "catamaze tick" to execute.',
      ],
    };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleTick(gameStateRef: { current: GameState }): Promise<CommandResult> {
  if (!gameStateRef.current.gameId) {
    return { output: ['No active game. Use "catamaze new" to start.'], error: true };
  }
  try {
    const response = await apiClient.executeTick(gameStateRef.current.gameId);
    gameStateRef.current.observation = response.observation;
    gameStateRef.current.queueSize = response.queue_size;
    const obs = response.observation;
    const output = [...renderGameState(obs, response.tick)];
    if (response.events.length > 0) {
      output.push('', ...renderEventLog(response.events));
    }
    if (obs.game_over) {
      output.push(...renderGameOver(obs.won, obs.alive));
    }
    return { output };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleClear(gameStateRef: { current: GameState }): Promise<CommandResult> {
  if (!gameStateRef.current.gameId) {
    return { output: ['No active game.'], error: true };
  }
  try {
    const response = await apiClient.clearQueue(gameStateRef.current.gameId);
    gameStateRef.current.queueSize = 0;
    return {
      output: [response.message, 'Queue cleared. You can start queueing new actions.'],
    };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleObserve(gameStateRef: { current: GameState }): Promise<CommandResult> {
  if (!gameStateRef.current.gameId) {
    return { output: ['No active game.'], error: true };
  }
  try {
    const response = await apiClient.observeGame(gameStateRef.current.gameId);
    return {
      output: ['=== CURRENT STATE ===', '', ...renderGameState(response.observation)],
    };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleResume(
  gameStateRef: { current: GameState },
  gameId: string | undefined
): Promise<CommandResult> {
  if (!gameId) {
    return { output: ['Usage: catamaze resume <game_id>'], error: true };
  }
  try {
    const response = await apiClient.resumeGame(gameId);
    gameStateRef.current = {
      gameId: response.game_id,
      observation: response.observation,
      queueSize: response.queue_size,
    };
    return {
      output: [
        '=== GAME RESUMED ===',
        `Game ID: ${response.game_id}, Queue: ${response.queue_size}`,
        '',
        ...renderGameState(response.observation),
      ],
    };
  } catch (error: any) {
    return { output: [`Error: ${error.message}`], error: true };
  }
}

export async function handleQueue(gameStateRef: { current: GameState }): Promise<CommandResult> {
  if (!gameStateRef.current.gameId) {
    return { output: ['No active game.'], error: true };
  }
  const queueSize = gameStateRef.current.queueSize;
  const status = queueSize > 0 ? `${queueSize} action(s) pending` : 'Queue is empty';
  return {
    output: [
      '╔════════════════════════════════════╗',
      '║         ACTION QUEUE               ║',
      '╠════════════════════════════════════╣',
      `║ Queue size: ${queueSize.toString().padEnd(22)} ║`,
      `║ ${status.padEnd(34)} ║`,
      '║ Each tick consumes 1 action        ║',
      '╚════════════════════════════════════╝',
    ],
  };
}
