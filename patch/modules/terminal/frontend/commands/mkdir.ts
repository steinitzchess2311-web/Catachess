import type { Command, CommandContext, CommandResult } from '../types';

export const mkdirCommand: Command = {
  name: 'mkdir',
  aliases: ['md'],
  description: 'Create a new directory (folder)',
  usage: 'mkdir <directory_name>',
  handler: (ctx: CommandContext): CommandResult => {
    const { args, system } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    if (args.length === 0) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'mkdir: missing operand',
      };
    }

    const dirName = args[0];

    // Validate directory name
    if (dirName.includes('/') || dirName.includes('\\')) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'mkdir: cannot create nested directories (use -p flag in real terminal)',
      };
    }

    // Return special token for async operation
    // Format: __ASYNC_MKDIR__:dirname
    return {
      output: [`__ASYNC_MKDIR__:${dirName}`],
    };
  },
};
