import type { Command, CommandContext, CommandResult, VirtualFileSystem, SystemType } from '../types';

// Import all commands
import { cdCommand } from './cd';
import { lsCommand, dirCommand } from './ls';
import { pwdCommand } from './pwd';
import { catCommand, typeCommand } from './cat';
import { echoCommand } from './echo';
import { whoamiCommand, hostnameCommand } from './whoami';
import { dateCommand, timeCommand } from './date';
import { historyCommand, dosKeyCommand, setCommandHistoryRef } from './history';
import { treeCommand } from './tree';
import { cowsayCommand, cowthinkCommand } from './cowsay';
import { fortuneCommand } from './fortune';
import { matrixCommand } from './matrix';
import { slCommand } from './sl';
import { neofetchCommand } from './neofetch';
import { colorCommand } from './color';
import {
  editCommand,
  formatCommand,
  deltreeCommand,
  pingCommand,
  memCommand,
  scandiskCommand,
  defragCommand,
} from './retro';
import { mkdirCommand } from './mkdir';
import { touchCommand } from './touch';
import { rmCommand, rmdirCommand } from './rm';

// Re-export history ref setter
export { setCommandHistoryRef };

// Command registry
const commands: Map<string, Command> = new Map();

// Register a command and its aliases
function registerCommand(cmd: Command): void {
  commands.set(cmd.name.toLowerCase(), cmd);
  if (cmd.aliases) {
    for (const alias of cmd.aliases) {
      commands.set(alias.toLowerCase(), cmd);
    }
  }
}

// Register all commands
// Basic file operations
registerCommand(cdCommand);
registerCommand(lsCommand);
registerCommand(dirCommand);
registerCommand(pwdCommand);
registerCommand(catCommand);
registerCommand(typeCommand);
registerCommand(treeCommand);
registerCommand(mkdirCommand);
registerCommand(touchCommand);
registerCommand(rmCommand);
registerCommand(rmdirCommand);

// Information commands
registerCommand(echoCommand);
registerCommand(whoamiCommand);
registerCommand(hostnameCommand);
registerCommand(dateCommand);
registerCommand(timeCommand);
registerCommand(historyCommand);
registerCommand(dosKeyCommand);

// Fun commands
registerCommand(cowsayCommand);
registerCommand(cowthinkCommand);
registerCommand(fortuneCommand);
registerCommand(matrixCommand);
registerCommand(slCommand);
registerCommand(neofetchCommand);
registerCommand(colorCommand);

// Retro/90s commands
registerCommand(editCommand);
registerCommand(formatCommand);
registerCommand(deltreeCommand);
registerCommand(pingCommand);
registerCommand(memCommand);
registerCommand(scandiskCommand);
registerCommand(defragCommand);

// Help command
const helpCommand: Command = {
  name: 'help',
  aliases: ['?', 'commands'],
  description: 'Display available commands',
  usage: 'help [command]',
  handler: (ctx: CommandContext): CommandResult => {
    const { system, args } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    if (args.length > 0) {
      const cmdName = args[0].toLowerCase();
      const cmd = commands.get(cmdName);
      if (cmd) {
        return {
          output: [
            `${cmd.name.toUpperCase()} - ${cmd.description}`,
            `Usage: ${cmd.usage}`,
            cmd.aliases?.length ? `Aliases: ${cmd.aliases.join(', ')}` : '',
          ].filter(Boolean),
        };
      }
      return {
        output: [],
        error: isDos ? 'Help not available for this command' : `help: no help for '${args[0]}'`,
      };
    }

    const lines: string[] = [];

    if (isDos) {
      lines.push('╔══════════════════════════════════════════════════════════╗');
      lines.push('║                  AVAILABLE COMMANDS                      ║');
      lines.push('╠══════════════════════════════════════════════════════════╣');
      lines.push('║  FILE OPERATIONS                                         ║');
      lines.push('║    CD        Change directory       DIR       List files ║');
      lines.push('║    TYPE      View file contents     TREE      Dir tree   ║');
      lines.push('║    MKDIR     Create directory       DEL       Delete     ║');
      lines.push('║    TOUCH     Create .study file     RMDIR     Remove dir ║');
      lines.push('║                                                          ║');
      lines.push('║  SYSTEM INFORMATION                                      ║');
      lines.push('║    VER       System version         MEM       Memory     ║');
      lines.push('║    DATE      Show date              TIME      Show time  ║');
      lines.push('║    HOSTNAME  Computer name                               ║');
      lines.push('║                                                          ║');
      lines.push('║  UTILITIES                                               ║');
      lines.push('║    CLS       Clear screen           ECHO      Print text ║');
      lines.push('║    HELP      This help              EDIT      Text editor║');
      lines.push('║    PING      Network test           SCANDISK  Check disk ║');
      lines.push('║    DEFRAG    Defragment             FORMAT    Format disk║');
      lines.push('║                                                          ║');
      lines.push('║  FUN STUFF                                               ║');
      lines.push('║    COWSAY    Talking cow            FORTUNE   Random quote║');
      lines.push('║    MATRIX    Digital rain           NEOFETCH  System info║');
      lines.push('║    COLOR     Change colors          SL        Choo choo! ║');
      lines.push('╚══════════════════════════════════════════════════════════╝');
    } else {
      lines.push('┌──────────────────────────────────────────────────────────┐');
      lines.push('│                  AVAILABLE COMMANDS                      │');
      lines.push('├──────────────────────────────────────────────────────────┤');
      lines.push('│  File Operations:                                        │');
      lines.push('│    cd        Change directory       ls        List files │');
      lines.push('│    pwd       Print working dir      cat       View file  │');
      lines.push('│    tree      Directory tree         mkdir     Create dir │');
      lines.push('│    touch     Create .study file     rm        Delete     │');
      lines.push('│                                                          │');
      lines.push('│  System Information:                                     │');
      lines.push('│    uname     System info            whoami    Username   │');
      lines.push('│    hostname  Computer name          date      Show date  │');
      lines.push('│    free      Memory usage           history   Cmd history│');
      lines.push('│                                                          │');
      lines.push('│  Utilities:                                              │');
      lines.push('│    clear     Clear screen           echo      Print text │');
      lines.push('│    help      This help              ping      Network    │');
      lines.push('│                                                          │');
      lines.push('│  Fun Stuff:                                              │');
      lines.push('│    cowsay    Talking cow            fortune   Random quote│');
      lines.push('│    matrix    Digital rain           neofetch  Sys info   │');
      lines.push('│    color     Change colors          sl        Train!     │');
      lines.push('└──────────────────────────────────────────────────────────┘');
    }

    lines.push('');
    lines.push('Type "help <command>" for detailed information.');

    return { output: lines };
  },
};

registerCommand(helpCommand);

// Clear command
const clearCommand: Command = {
  name: 'clear',
  aliases: ['cls'],
  description: 'Clear the terminal screen',
  usage: 'clear',
  handler: (): CommandResult => {
    return { output: ['__CLEAR__'] }; // Special token handled by terminal
  },
};

registerCommand(clearCommand);

// Version/uname command
const versionCommand: Command = {
  name: 'ver',
  aliases: ['uname', 'version'],
  description: 'Display system version',
  usage: 'ver',
  handler: (ctx: CommandContext): CommandResult => {
    const { system, flags } = ctx;

    // Handle uname -a style
    if (flags['a']) {
      switch (system) {
        case 'linux':
          return { output: ['Linux localhost 5.15.0-generic #1 SMP x86_64 GNU/Linux'] };
        case 'mac':
          return { output: ['Darwin Mac.local 22.0.0 Darwin Kernel Version 22.0.0: x86_64'] };
        default:
          break;
      }
    }

    switch (system) {
      case 'dos':
        return {
          output: [
            '',
            'MS-DOS Version 6.22',
            '',
          ],
        };
      case 'win95':
        return {
          output: [
            '',
            'Microsoft Windows 95 [Version 4.00.950]',
            '(C) Copyright Microsoft Corp 1981-1995.',
            '',
          ],
        };
      case 'linux':
        return { output: ['Linux'] };
      case 'mac':
        return { output: ['Darwin'] };
      default:
        return { output: ['Unknown System'] };
    }
  },
};

registerCommand(versionCommand);

// Exit command
const exitCommand: Command = {
  name: 'exit',
  aliases: ['quit', 'logout', 'bye'],
  description: 'Exit the terminal (simulated)',
  usage: 'exit',
  handler: (ctx: CommandContext): CommandResult => {
    const { system } = ctx;
    const isDos = system === 'dos' || system === 'win95';

    return {
      output: [
        '',
        isDos
          ? 'Type EXIT to quit and return to Windows.'
          : 'logout',
        '',
        '[This is a virtual terminal - use the X button to close]',
      ],
    };
  },
};

registerCommand(exitCommand);

// About command
const aboutCommand: Command = {
  name: 'about',
  aliases: ['credits'],
  description: 'About this terminal',
  usage: 'about',
  handler: (): CommandResult => {
    return {
      output: [
        '',
        '  ╔════════════════════════════════════════════════════╗',
        '  ║                                                    ║',
        '  ║   CataChess Virtual Terminal                       ║',
        '  ║   Version 1.0.0                                    ║',
        '  ║                                                    ║',
        '  ║   A retro terminal emulator for the modern web.    ║',
        '  ║   Supports MS-DOS, Windows 95, Linux, and macOS    ║',
        '  ║   terminal styles.                                 ║',
        '  ║                                                    ║',
        '  ║   Made with nostalgia and love for the 90s.        ║',
        '  ║                                                    ║',
        '  ╚════════════════════════════════════════════════════╝',
        '',
      ],
    };
  },
};

registerCommand(aboutCommand);

// Parse command line into command, args, and flags
function parseCommandLine(input: string): { command: string; args: string[]; flags: Record<string, boolean | string> } {
  const parts = input.trim().split(/\s+/);
  const command = parts[0]?.toLowerCase() || '';
  const args: string[] = [];
  const flags: Record<string, boolean | string> = {};

  for (let i = 1; i < parts.length; i++) {
    const part = parts[i];
    if (part.startsWith('--')) {
      const [key, value] = part.slice(2).split('=');
      flags[key] = value || true;
    } else if (part.startsWith('-') && part.length > 1 && !part.match(/^-\d/)) {
      // Handle combined flags like -la, but not negative numbers
      for (const char of part.slice(1)) {
        flags[char] = true;
      }
    } else if (part.startsWith('/') && (command === 'dir' || command === 'doskey')) {
      // DOS-style flags
      flags[part.slice(1).toLowerCase()] = true;
    } else {
      args.push(part);
    }
  }

  return { command, args, flags };
}

// Execute a command
export function executeCommand(
  input: string,
  cwd: string,
  system: SystemType,
  fs: VirtualFileSystem
): CommandResult {
  const { command, args, flags } = parseCommandLine(input);

  if (!command) {
    return { output: [] };
  }

  const cmd = commands.get(command);
  if (!cmd) {
    const errorMsg = system === 'dos' || system === 'win95'
      ? `'${command}' is not recognized as an internal or external command,\noperable program or batch file.`
      : `${command}: command not found`;
    return { output: [], error: errorMsg };
  }

  const ctx: CommandContext = {
    cwd,
    system,
    args,
    flags,
  };

  return cmd.handler(ctx, fs);
}

export function getAvailableCommands(): Command[] {
  // Return unique commands (no aliases)
  const seen = new Set<string>();
  const result: Command[] = [];

  for (const cmd of commands.values()) {
    if (!seen.has(cmd.name)) {
      seen.add(cmd.name);
      result.push(cmd);
    }
  }

  return result;
}

export function getCommand(name: string): Command | undefined {
  return commands.get(name.toLowerCase());
}
