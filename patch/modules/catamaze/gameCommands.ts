/**
 * CataMaze game commands for terminal
 */
import { apiClient, Observation } from './apiClient';
import type { Command, CommandContext, CommandResult } from '@patch/modules/terminal/types';

interface GameState {
  gameId: string | null;
  observation: Observation | null;
  queueSize: number;
}

const renderVision = (vision: string[][]): string[] => vision.map(row => row.join(' '));

export function createGameCommands(gameStateRef: { current: GameState }): Command[] {
  const newGameCommand: Command = {
    name: 'new',
    description: 'Start a new game',
    usage: 'new',
    handler: async (): Promise<CommandResult> => {
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
            `HP: ${response.observation.hp}  Ammo: ${response.observation.ammo}`,
            `Position: (${response.observation.position.x}, ${response.observation.position.y})`,
            '',
            'Vision:',
            ...renderVision(response.observation.vision),
            '',
            'Type "help" for commands, or use: move, shoot, tick',
          ],
        };
      } catch (error: any) {
        return { output: [`Error: ${error.message}`], error: true };
      }
    },
  };

  const moveCommand: Command = {
    name: 'move',
    aliases: ['m'],
    description: 'Queue a movement action',
    usage: 'move <up|down|left|right>',
    handler: async (ctx: CommandContext): Promise<CommandResult> => {
      if (!gameStateRef.current.gameId) {
        return { output: ['No active game. Use "new" to start.'], error: true };
      }

      const dir = ctx.args[0]?.toUpperCase();
      if (!['UP', 'DOWN', 'LEFT', 'RIGHT'].includes(dir)) {
        return { output: ['Usage: move <up|down|left|right>'], error: true };
      }

      try {
        const response = await apiClient.submitAction(
          gameStateRef.current.gameId,
          `MOVE_${dir}`
        );
        gameStateRef.current.queueSize = response.queue_size;

        return {
          output: [
            `Action queued: MOVE_${dir}`,
            `Queue size: ${response.queue_size}`,
            'Use "tick" to execute.',
          ],
        };
      } catch (error: any) {
        return { output: [`Error: ${error.message}`], error: true };
      }
    },
  };

  const shootCommand: Command = {
    name: 'shoot',
    aliases: ['s'],
    description: 'Queue a shooting action',
    usage: 'shoot <up|down|left|right>',
    handler: async (ctx: CommandContext): Promise<CommandResult> => {
      if (!gameStateRef.current.gameId) {
        return { output: ['No active game. Use "new" to start.'], error: true };
      }

      const dir = ctx.args[0]?.toUpperCase();
      if (!['UP', 'DOWN', 'LEFT', 'RIGHT'].includes(dir)) {
        return { output: ['Usage: shoot <up|down|left|right>'], error: true };
      }

      try {
        const response = await apiClient.submitAction(
          gameStateRef.current.gameId,
          `SHOOT_${dir}`
        );
        gameStateRef.current.queueSize = response.queue_size;

        return {
          output: [
            `Action queued: SHOOT_${dir}`,
            `Queue size: ${response.queue_size}`,
            'Use "tick" to execute.',
          ],
        };
      } catch (error: any) {
        return { output: [`Error: ${error.message}`], error: true };
      }
    },
  };

  const tickCommand: Command = {
    name: 'tick',
    aliases: ['t'],
    description: 'Execute one game tick',
    usage: 'tick',
    handler: async (): Promise<CommandResult> => {
      if (!gameStateRef.current.gameId) {
        return { output: ['No active game. Use "new" to start.'], error: true };
      }

      try {
        const response = await apiClient.executeTick(gameStateRef.current.gameId);
        gameStateRef.current.observation = response.observation;
        gameStateRef.current.queueSize = response.queue_size;

        const obs = response.observation;
        const output = [
          `=== TICK ${response.tick} ===`,
          `HP: ${obs.hp}  Ammo: ${obs.ammo}  Queue: ${response.queue_size}`,
          `Position: (${obs.position.x}, ${obs.position.y})`,
        ];

        if (response.events.length > 0) {
          output.push('', 'Events:');
          response.events.forEach(e => output.push(`  ${e}`));
        }

        if (obs.last_sound) {
          output.push('', `Sound: ${obs.last_sound}`);
        }

        output.push('', 'Vision:', ...renderVision(obs.vision));

        if (obs.game_over) {
          output.push('', '=== GAME OVER ===');
          if (obs.won) {
            output.push('YOU WON! Congratulations!');
          } else if (!obs.alive) {
            output.push('You died. Better luck next time!');
          }
        }

        return { output };
      } catch (error: any) {
        return { output: [`Error: ${error.message}`], error: true };
      }
    },
  };

  const observeCommand: Command = {
    name: 'observe',
    aliases: ['obs', 'o'],
    description: 'View current game state',
    usage: 'observe',
    handler: async (): Promise<CommandResult> => {
      if (!gameStateRef.current.gameId) {
        return { output: ['No active game. Use "new" to start.'], error: true };
      }

      try {
        const response = await apiClient.observeGame(gameStateRef.current.gameId);
        const obs = response.observation;

        return {
          output: [
            '=== CURRENT STATE ===',
            `HP: ${obs.hp}  Ammo: ${obs.ammo}  Tick: ${obs.time}`,
            `Position: (${obs.position.x}, ${obs.position.y})`,
            `Alive: ${obs.alive}  Won: ${obs.won}`,
            '',
            'Vision:',
            ...renderVision(obs.vision),
          ],
        };
      } catch (error: any) {
        return { output: [`Error: ${error.message}`], error: true };
      }
    },
  };

  return [newGameCommand, moveCommand, shootCommand, tickCommand, observeCommand];
}
