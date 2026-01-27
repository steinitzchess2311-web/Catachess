/**
 * CataMaze game command for terminal
 */
import type { Command, CommandContext, CommandResult } from '../types';
import { createCataMazeCommand } from '@patch/modules/catamaze';
import { useRef } from 'react';

// Game state shared across command invocations
const gameStateRef = {
  current: {
    gameId: null as string | null,
    observation: null as any,
    queueSize: 0,
  },
};

// Create the catamaze command using the factory
const cataMazeCmd = createCataMazeCommand(gameStateRef);

// Wrap it to match the terminal command interface
export const cataMazeCommand: Command = {
  name: cataMazeCmd.name,
  aliases: cataMazeCmd.aliases,
  description: cataMazeCmd.description,
  usage: cataMazeCmd.usage,
  handler: async (ctx: CommandContext): Promise<CommandResult> => {
    // Convert terminal CommandContext to the catamaze CommandContext
    const cataMazeCtx = {
      args: ctx.args,
      flags: ctx.flags,
      cwd: ctx.cwd,
      system: ctx.system,
    };

    // Call the catamaze handler
    const result = await cataMazeCmd.handler(cataMazeCtx);

    // Convert result
    return {
      output: Array.isArray(result.output) ? result.output : [result.output],
      error: result.error,
    };
  },
};
