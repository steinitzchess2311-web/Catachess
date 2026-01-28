/**
 * CataMaze Terminal Frontend
 * Integrates with CataChess terminal module
 */
import React, { useRef } from 'react';
import { TerminalLauncher } from '@patch/modules/terminal';
import { Observation } from './apiClient';
import { createCataMazeCommand } from './commands/catamaze';

interface GameState {
  gameId: string | null;
  observation: Observation | null;
  queueSize: number;
}

export function CataMazeTerminal() {
  const gameState = useRef<GameState>({
    gameId: null,
    observation: null,
    queueSize: 0,
  });

  const cataMazeCommand = createCataMazeCommand(gameState);

  return (
    <TerminalLauncher
      initialSystem="dos"
      customCommands={[cataMazeCommand]}
    />
  );
}

export default CataMazeTerminal;
