import type { Command, CommandContext, CommandResult } from '../types';

export const rmCommand: Command = {
  name: 'rm',
  aliases: ['del', 'delete', 'erase'],
  description: 'Delete a file or directory',
  usage: 'rm <file_or_directory>',
  handler: (ctx: CommandContext): CommandResult => {
    const { args, flags, system } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    if (args.length === 0) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'rm: missing operand',
      };
    }

    const target = args[0];
    const force = flags['f'] === true || flags['force'] === true;

    // If -f flag is used, skip confirmation
    if (force) {
      return {
        output: [`__ASYNC_RM_FORCE__:${target}`],
      };
    }

    // Return special token for confirmation prompt
    // Format: __CONFIRM_RM__:target
    return {
      output: [`__CONFIRM_RM__:${target}`],
    };
  },
};

export const rmdirCommand: Command = {
  name: 'rmdir',
  aliases: ['rd'],
  description: 'Remove a directory',
  usage: 'rmdir <directory>',
  handler: (ctx: CommandContext): CommandResult => {
    const { args, system } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    if (args.length === 0) {
      return {
        output: [],
        error: isDos
          ? 'The syntax of the command is incorrect.'
          : 'rmdir: missing operand',
      };
    }

    const target = args[0];

    // Return special token for confirmation prompt
    return {
      output: [`__CONFIRM_RM__:${target}`],
    };
  },
};
