import type { Command, CommandContext, CommandResult } from '../types';

export const touchCommand: Command = {
  name: 'touch',
  aliases: ['create'],
  description: 'Create a new study file (.study)',
  usage: 'touch <filename.study>',
  handler: (ctx: CommandContext): CommandResult => {
    const { args, system } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    if (args.length === 0) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'touch: missing file operand',
      };
    }

    let fileName = args[0];

    // Auto-add .study extension if not present
    if (!fileName.toLowerCase().endsWith('.study')) {
      fileName = `${fileName}.study`;
    }

    // Remove .study for the title
    const title = fileName.replace(/\.study$/i, '');

    // Validate file name
    if (title.includes('/') || title.includes('\\')) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'touch: invalid file name',
      };
    }

    // Return special token for async operation
    // Format: __ASYNC_TOUCH__:filename
    return {
      output: [`__ASYNC_TOUCH__:${fileName}`],
    };
  },
};
