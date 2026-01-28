/**
 * ASCII UI renderer for CataMaze terminal
 */
import { Observation } from './apiClient';

export function renderGameState(obs: Observation, tick?: number): string[] {
  const output: string[] = [];

  // Header
  if (tick !== undefined) {
    output.push(`╔═══ TICK ${tick} ${'═'.repeat(Math.max(0, 30 - tick.toString().length))}╗`);
  } else {
    output.push('╔════════════════════════════════════╗');
  }

  // Stats bar
  const hpBar = renderBar('HP', obs.hp, 5, '♥');
  const ammoBar = renderBar('Ammo', obs.ammo, 3, '●');
  output.push(`║ ${hpBar}  ${ammoBar} ║`);
  output.push(`║ Time: ${obs.time}  Pos: (${obs.position.x},${obs.position.y})${' '.repeat(Math.max(0, 12 - obs.time.toString().length - obs.position.x.toString().length - obs.position.y.toString().length))}║`);

  // Vision section
  output.push('╠════════════════════════════════════╣');
  output.push('║          VISION (5x5)              ║');
  output.push('╠════════════════════════════════════╣');

  const visionLines = renderVision(obs.vision);
  visionLines.forEach(line => {
    const paddedLine = line.padEnd(34);
    output.push(`║ ${paddedLine} ║`);
  });

  // Sound section
  output.push('╠════════════════════════════════════╣');
  if (obs.last_sound) {
    const soundLine = `Sound: ${obs.last_sound}`.padEnd(34);
    output.push(`║ ${soundLine} ║`);
  } else {
    output.push('║ Sound: [silence]                   ║');
  }

  // Status section
  output.push('╠════════════════════════════════════╣');
  const aliveStatus = obs.alive ? '✓ Alive' : '✗ Dead';
  const wonStatus = obs.won ? '★ WON' : '- Playing';
  const statusLine = `${aliveStatus}  ${wonStatus}`.padEnd(34);
  output.push(`║ ${statusLine} ║`);

  // Footer
  output.push('╚════════════════════════════════════╝');

  return output;
}

function renderBar(label: string, current: number, max: number, symbol: string): string {
  const filled = symbol.repeat(current);
  const empty = '·'.repeat(max - current);
  return `${label}: ${filled}${empty}`;
}

export function renderVision(vision: string[][]): string[] {
  const lines: string[] = [];

  for (let i = 0; i < vision.length; i++) {
    const row = vision[i];
    const line = row.map(cell => formatCell(cell)).join(' ');
    lines.push(line);
  }

  return lines;
}

function formatCell(cell: string): string {
  // Map game symbols to visual representation
  switch (cell) {
    case '#':
      return '█'; // Wall
    case '.':
      return '·'; // Empty
    case '@':
      return '@'; // Player
    case 'P':
      return 'P'; // Agent
    case 'S':
      return 'S'; // Start
    case 'E':
      return 'E'; // Exit
    case 'A':
      return 'A'; // Ammo
    case 'o':
      return 'o'; // Bullet
    default:
      return cell;
  }
}

export function renderEventLog(events: string[]): string[] {
  if (events.length === 0) {
    return ['No events this tick.'];
  }

  const output: string[] = ['╔════════════════════════════════════╗'];
  output.push('║            EVENT LOG               ║');
  output.push('╠════════════════════════════════════╣');

  events.forEach((event, idx) => {
    const num = `${idx + 1}.`.padEnd(3);
    const text = event.substring(0, 29); // Truncate long events
    const line = `${num} ${text}`.padEnd(34);
    output.push(`║ ${line} ║`);
  });

  output.push('╚════════════════════════════════════╝');

  return output;
}

export function renderGameOver(won: boolean, alive: boolean): string[] {
  const output: string[] = [];

  output.push('');
  output.push('╔════════════════════════════════════╗');
  output.push('║                                    ║');

  if (won) {
    output.push('║         ★ YOU WON! ★               ║');
    output.push('║                                    ║');
    output.push('║   You escaped the maze!            ║');
  } else if (!alive) {
    output.push('║         ✗ GAME OVER ✗              ║');
    output.push('║                                    ║');
    output.push('║   You died in the maze...          ║');
  }

  output.push('║                                    ║');
  output.push('╚════════════════════════════════════╝');
  output.push('');
  output.push('Type "catamaze new" to play again.');

  return output;
}

export function renderHelp(): string[] {
  return [
    '╔════════════════════════════════════╗',
    '║        CATAMAZE COMMANDS           ║',
    '╠════════════════════════════════════╣',
    '║ catamaze new                       ║',
    '║   Start a new game                 ║',
    '║                                    ║',
    '║ catamaze action <keys>             ║',
    '║   Queue action(s)                  ║',
    '║   Keys: w/a/s/d (move)             ║',
    '║         i/j/k/l (shoot)            ║',
    '║         space (wait)               ║',
    '║   Example: wasd (queue 4 moves)    ║',
    '║                                    ║',
    '║ catamaze tick                      ║',
    '║   Execute one tick                 ║',
    '║                                    ║',
    '║ catamaze queue                     ║',
    '║   View action queue                ║',
    '║                                    ║',
    '║ catamaze clear                     ║',
    '║   Clear action queue (ESC)         ║',
    '║                                    ║',
    '║ catamaze observe                   ║',
    '║   View current state               ║',
    '║                                    ║',
    '║ catamaze resume <id>               ║',
    '║   Resume a saved game              ║',
    '╚════════════════════════════════════╝',
  ];
}

export function renderSimpleVision(vision: string[][]): string[] {
  return vision.map(row => row.join(' '));
}
