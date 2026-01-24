import React, { createContext, useContext, useReducer, useCallback, ReactNode, useRef } from 'react';
import type { TerminalState, TerminalLine, SystemType, WindowState } from './types';
import { getSystem } from './systems';
import { executeCommand } from './commands';
import { virtualFS } from './filesystem';
import {
  createFolder,
  createStudy,
  deleteNode,
  getNodeChildren,
  getRootNodes,
  resolvePathToNode,
  invalidatePathCache,
  type WorkspaceNode,
} from './api';

// =============================================================================
// State Types
// =============================================================================

interface PendingConfirmation {
  type: 'delete';
  target: string;
  nodeId?: string;
  message: string;
}

interface FullTerminalState {
  terminal: TerminalState;
  window: WindowState;
  pendingConfirmation: PendingConfirmation | null;
  isProcessing: boolean;
  currentNodeId: string | null; // Current directory node ID
  nodeCache: Map<string, WorkspaceNode>; // Path -> Node cache
}

// =============================================================================
// Actions
// =============================================================================

type TerminalAction =
  | { type: 'SET_SYSTEM'; system: SystemType }
  | { type: 'EXECUTE_COMMAND'; input: string }
  | { type: 'ADD_OUTPUT'; lines: TerminalLine[] }
  | { type: 'CLEAR' }
  | { type: 'NAVIGATE_HISTORY'; direction: 'up' | 'down' }
  | { type: 'TOGGLE_EFFECT'; effect: 'scanlines' | 'sound' | 'crtGlow' }
  | { type: 'SET_BOOTING'; isBooting: boolean }
  | { type: 'SET_WINDOW_POSITION'; x: number; y: number }
  | { type: 'SET_WINDOW_SIZE'; width: number; height: number }
  | { type: 'TOGGLE_MAXIMIZE' }
  | { type: 'TOGGLE_MINIMIZE' }
  | { type: 'SET_VISIBLE'; isVisible: boolean }
  | { type: 'SET_PENDING_CONFIRMATION'; confirmation: PendingConfirmation | null }
  | { type: 'SET_PROCESSING'; isProcessing: boolean }
  | { type: 'SET_CURRENT_NODE'; nodeId: string | null }
  | { type: 'SET_CWD'; cwd: string };

// =============================================================================
// Initial State
// =============================================================================

function createInitialState(system: SystemType = 'dos'): FullTerminalState {
  const config = getSystem(system);
  const startupLines: TerminalLine[] = config.startupMessages.map((msg, i) => ({
    id: `startup-${i}`,
    type: 'system',
    content: msg,
    timestamp: Date.now(),
  }));

  return {
    terminal: {
      system,
      cwd: '/',
      username: 'user',
      hostname: 'localhost',
      history: startupLines,
      commandHistory: [],
      commandHistoryIndex: -1,
      isBooting: false,
      effects: {
        scanlines: true,
        sound: false,
        crtGlow: true,
      },
    },
    window: {
      position: { x: 100, y: 100 },
      size: { width: 680, height: 480 },
      isMaximized: false,
      isMinimized: false,
      isVisible: true,
    },
    pendingConfirmation: null,
    isProcessing: false,
    currentNodeId: null,
    nodeCache: new Map(),
  };
}

// =============================================================================
// Reducer
// =============================================================================

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function terminalReducer(state: FullTerminalState, action: TerminalAction): FullTerminalState {
  switch (action.type) {
    case 'SET_SYSTEM': {
      const config = getSystem(action.system);
      const startupLines: TerminalLine[] = config.startupMessages.map((msg, i) => ({
        id: `startup-${i}-${Date.now()}`,
        type: 'system',
        content: msg,
        timestamp: Date.now(),
      }));

      return {
        ...state,
        terminal: {
          ...state.terminal,
          system: action.system,
          cwd: '/',
          history: startupLines,
          commandHistory: [],
          commandHistoryIndex: -1,
        },
        currentNodeId: null,
      };
    }

    case 'EXECUTE_COMMAND': {
      const { input } = action;
      const { terminal } = state;
      const config = getSystem(terminal.system);
      const prompt = config.prompt(terminal.cwd, terminal.username);

      const inputLine: TerminalLine = {
        id: generateId(),
        type: 'input',
        content: input,
        prompt,
        timestamp: Date.now(),
      };

      const result = executeCommand(input, terminal.cwd, terminal.system, virtualFS);

      if (result.output.length === 1 && result.output[0] === '__CLEAR__') {
        return {
          ...state,
          terminal: {
            ...terminal,
            history: [],
            commandHistory: [...terminal.commandHistory, input],
            commandHistoryIndex: -1,
          },
        };
      }

      const outputLines: TerminalLine[] = [];

      if (result.error) {
        outputLines.push({
          id: generateId(),
          type: 'error',
          content: result.error,
          timestamp: Date.now(),
        });
      } else {
        for (const line of result.output) {
          outputLines.push({
            id: generateId(),
            type: 'output',
            content: line,
            timestamp: Date.now(),
          });
        }
      }

      return {
        ...state,
        terminal: {
          ...terminal,
          cwd: result.newCwd || terminal.cwd,
          history: [...terminal.history, inputLine, ...outputLines],
          commandHistory: input.trim() ? [...terminal.commandHistory, input] : terminal.commandHistory,
          commandHistoryIndex: -1,
        },
      };
    }

    case 'ADD_OUTPUT': {
      return {
        ...state,
        terminal: {
          ...state.terminal,
          history: [...state.terminal.history, ...action.lines],
        },
      };
    }

    case 'CLEAR': {
      return {
        ...state,
        terminal: {
          ...state.terminal,
          history: [],
        },
      };
    }

    case 'NAVIGATE_HISTORY': {
      const { commandHistory, commandHistoryIndex } = state.terminal;
      if (commandHistory.length === 0) return state;

      let newIndex: number;
      if (action.direction === 'up') {
        newIndex = commandHistoryIndex === -1
          ? commandHistory.length - 1
          : Math.max(0, commandHistoryIndex - 1);
      } else {
        newIndex = commandHistoryIndex === -1
          ? -1
          : commandHistoryIndex >= commandHistory.length - 1
            ? -1
            : commandHistoryIndex + 1;
      }

      return {
        ...state,
        terminal: {
          ...state.terminal,
          commandHistoryIndex: newIndex,
        },
      };
    }

    case 'TOGGLE_EFFECT': {
      return {
        ...state,
        terminal: {
          ...state.terminal,
          effects: {
            ...state.terminal.effects,
            [action.effect]: !state.terminal.effects[action.effect],
          },
        },
      };
    }

    case 'SET_BOOTING': {
      return {
        ...state,
        terminal: {
          ...state.terminal,
          isBooting: action.isBooting,
        },
      };
    }

    case 'SET_WINDOW_POSITION': {
      return {
        ...state,
        window: {
          ...state.window,
          position: { x: action.x, y: action.y },
        },
      };
    }

    case 'SET_WINDOW_SIZE': {
      return {
        ...state,
        window: {
          ...state.window,
          size: { width: action.width, height: action.height },
        },
      };
    }

    case 'TOGGLE_MAXIMIZE': {
      return {
        ...state,
        window: {
          ...state.window,
          isMaximized: !state.window.isMaximized,
        },
      };
    }

    case 'TOGGLE_MINIMIZE': {
      return {
        ...state,
        window: {
          ...state.window,
          isMinimized: !state.window.isMinimized,
        },
      };
    }

    case 'SET_VISIBLE': {
      return {
        ...state,
        window: {
          ...state.window,
          isVisible: action.isVisible,
        },
      };
    }

    case 'SET_PENDING_CONFIRMATION': {
      return {
        ...state,
        pendingConfirmation: action.confirmation,
      };
    }

    case 'SET_PROCESSING': {
      return {
        ...state,
        isProcessing: action.isProcessing,
      };
    }

    case 'SET_CURRENT_NODE': {
      return {
        ...state,
        currentNodeId: action.nodeId,
      };
    }

    case 'SET_CWD': {
      return {
        ...state,
        terminal: {
          ...state.terminal,
          cwd: action.cwd,
        },
      };
    }

    default:
      return state;
  }
}

// =============================================================================
// Context
// =============================================================================

interface TerminalContextValue {
  state: FullTerminalState;
  executeCommand: (input: string) => void;
  setSystem: (system: SystemType) => void;
  clear: () => void;
  navigateHistory: (direction: 'up' | 'down') => void;
  toggleEffect: (effect: 'scanlines' | 'sound' | 'crtGlow') => void;
  setWindowPosition: (x: number, y: number) => void;
  setWindowSize: (width: number, height: number) => void;
  toggleMaximize: () => void;
  toggleMinimize: () => void;
  setVisible: (isVisible: boolean) => void;
  getHistoryCommand: () => string | null;
  confirmAction: (confirmed: boolean) => void;
}

const TerminalContext = createContext<TerminalContextValue | null>(null);

// =============================================================================
// Provider
// =============================================================================

interface TerminalProviderProps {
  children: ReactNode;
  initialSystem?: SystemType;
}

export function TerminalProvider({ children, initialSystem = 'dos' }: TerminalProviderProps) {
  const [state, dispatch] = useReducer(terminalReducer, createInitialState(initialSystem));
  const pendingActionRef = useRef<{ target: string; nodeId?: string } | null>(null);

  const addOutput = useCallback((lines: TerminalLine[]) => {
    dispatch({ type: 'ADD_OUTPUT', lines });
  }, []);

  const addLine = useCallback((content: string, type: 'output' | 'error' | 'system' = 'output') => {
    addOutput([{
      id: generateId(),
      type,
      content,
      timestamp: Date.now(),
    }]);
  }, [addOutput]);

  // Handle async mkdir
  const handleMkdir = useCallback(async (dirName: string) => {
    dispatch({ type: 'SET_PROCESSING', isProcessing: true });

    try {
      const parentNodeId = state.currentNodeId;
      const result = await createFolder(dirName, parentNodeId || undefined);

      if (result) {
        addLine(`Directory created: ${dirName}`);
        invalidatePathCache(state.terminal.cwd);
      } else {
        addLine(`Failed to create directory: ${dirName}`, 'error');
      }
    } catch (e: any) {
      addLine(`Error: ${e.message || 'Failed to create directory'}`, 'error');
    } finally {
      dispatch({ type: 'SET_PROCESSING', isProcessing: false });
    }
  }, [state.currentNodeId, state.terminal.cwd, addLine]);

  // Handle async touch (create study)
  const handleTouch = useCallback(async (fileName: string) => {
    dispatch({ type: 'SET_PROCESSING', isProcessing: true });

    try {
      const title = fileName.replace(/\.study$/i, '');
      const parentNodeId = state.currentNodeId;
      const result = await createStudy(title, parentNodeId || undefined);

      if (result) {
        addLine(`Study created: ${fileName}`);
        invalidatePathCache(state.terminal.cwd);
      } else {
        addLine(`Failed to create study: ${fileName}`, 'error');
      }
    } catch (e: any) {
      addLine(`Error: ${e.message || 'Failed to create study'}`, 'error');
    } finally {
      dispatch({ type: 'SET_PROCESSING', isProcessing: false });
    }
  }, [state.currentNodeId, state.terminal.cwd, addLine]);

  // Handle delete with confirmation
  const handleDeleteConfirm = useCallback(async (target: string) => {
    const isDos = state.terminal.system === 'dos' || state.terminal.system === 'win95';

    // Find the node to delete
    const targetPath = target.startsWith('/')
      ? target
      : `${state.terminal.cwd}/${target}`.replace(/\/+/g, '/');

    const node = await resolvePathToNode(targetPath);

    if (!node) {
      addLine(isDos
        ? 'File Not Found'
        : `rm: cannot remove '${target}': No such file or directory`,
        'error'
      );
      return;
    }

    // Store pending action and show confirmation
    pendingActionRef.current = { target, nodeId: node.id };

    const typeLabel = node.node_type === 'folder' ? 'directory' : 'study';

    dispatch({
      type: 'SET_PENDING_CONFIRMATION',
      confirmation: {
        type: 'delete',
        target,
        nodeId: node.id,
        message: isDos
          ? `Delete ${typeLabel} "${target}"? (Y/N)`
          : `rm: remove ${typeLabel} '${target}'? (y/n)`,
      },
    });

    addLine(isDos
      ? `Delete ${typeLabel} "${target}"? (Y/N)`
      : `rm: remove ${typeLabel} '${target}'? (y/n)`,
      'system'
    );
  }, [state.terminal.system, state.terminal.cwd, addLine]);

  // Handle delete force (no confirmation)
  const handleDeleteForce = useCallback(async (target: string) => {
    dispatch({ type: 'SET_PROCESSING', isProcessing: true });

    try {
      const targetPath = target.startsWith('/')
        ? target
        : `${state.terminal.cwd}/${target}`.replace(/\/+/g, '/');

      const node = await resolvePathToNode(targetPath);

      if (!node) {
        addLine(`rm: cannot remove '${target}': No such file or directory`, 'error');
        return;
      }

      await deleteNode(node.id, node.version);
      addLine(`Deleted: ${target}`);
      invalidatePathCache(state.terminal.cwd);
    } catch (e: any) {
      addLine(`Error: ${e.message || 'Failed to delete'}`, 'error');
    } finally {
      dispatch({ type: 'SET_PROCESSING', isProcessing: false });
    }
  }, [state.terminal.cwd, addLine]);

  // Confirm or cancel pending action
  const confirmAction = useCallback(async (confirmed: boolean) => {
    const pending = state.pendingConfirmation;
    if (!pending) return;

    dispatch({ type: 'SET_PENDING_CONFIRMATION', confirmation: null });

    if (!confirmed) {
      addLine('Cancelled.');
      pendingActionRef.current = null;
      return;
    }

    if (pending.type === 'delete' && pending.nodeId) {
      dispatch({ type: 'SET_PROCESSING', isProcessing: true });

      try {
        await deleteNode(pending.nodeId);
        addLine(`Deleted: ${pending.target}`);
        invalidatePathCache(state.terminal.cwd);
      } catch (e: any) {
        addLine(`Error: ${e.message || 'Failed to delete'}`, 'error');
      } finally {
        dispatch({ type: 'SET_PROCESSING', isProcessing: false });
        pendingActionRef.current = null;
      }
    }
  }, [state.pendingConfirmation, state.terminal.cwd, addLine]);

  // Main command executor
  const execCommand = useCallback(async (input: string) => {
    // If there's a pending confirmation, handle y/n
    if (state.pendingConfirmation) {
      const answer = input.trim().toLowerCase();
      if (answer === 'y' || answer === 'yes') {
        confirmAction(true);
      } else {
        confirmAction(false);
      }
      return;
    }

    const { terminal } = state;
    const config = getSystem(terminal.system);
    const prompt = config.prompt(terminal.cwd, terminal.username);

    // Add input line
    addOutput([{
      id: generateId(),
      type: 'input',
      content: input,
      prompt,
      timestamp: Date.now(),
    }]);

    // Execute the command
    const result = executeCommand(input, terminal.cwd, terminal.system, virtualFS);

    // Handle special async commands
    if (result.output.length === 1) {
      const output = result.output[0];

      if (output === '__CLEAR__') {
        dispatch({ type: 'CLEAR' });
        dispatch({
          type: 'SET_CWD',
          cwd: terminal.cwd,
        });
        return;
      }

      if (output.startsWith('__ASYNC_MKDIR__:')) {
        const dirName = output.replace('__ASYNC_MKDIR__:', '');
        await handleMkdir(dirName);
        return;
      }

      if (output.startsWith('__ASYNC_TOUCH__:')) {
        const fileName = output.replace('__ASYNC_TOUCH__:', '');
        await handleTouch(fileName);
        return;
      }

      if (output.startsWith('__CONFIRM_RM__:')) {
        const target = output.replace('__CONFIRM_RM__:', '');
        await handleDeleteConfirm(target);
        return;
      }

      if (output.startsWith('__ASYNC_RM_FORCE__:')) {
        const target = output.replace('__ASYNC_RM_FORCE__:', '');
        await handleDeleteForce(target);
        return;
      }
    }

    // Normal output
    if (result.error) {
      addLine(result.error, 'error');
    } else {
      for (const line of result.output) {
        addLine(line, 'output');
      }
    }

    // Update cwd if changed
    if (result.newCwd) {
      dispatch({ type: 'SET_CWD', cwd: result.newCwd });
    }

    // Update command history
    if (input.trim()) {
      dispatch({
        type: 'NAVIGATE_HISTORY',
        direction: 'down', // Reset index
      });
    }
  }, [
    state,
    addOutput,
    addLine,
    handleMkdir,
    handleTouch,
    handleDeleteConfirm,
    handleDeleteForce,
    confirmAction,
  ]);

  const setSystem = useCallback((system: SystemType) => {
    dispatch({ type: 'SET_SYSTEM', system });
  }, []);

  const clear = useCallback(() => {
    dispatch({ type: 'CLEAR' });
  }, []);

  const navigateHistory = useCallback((direction: 'up' | 'down') => {
    dispatch({ type: 'NAVIGATE_HISTORY', direction });
  }, []);

  const toggleEffect = useCallback((effect: 'scanlines' | 'sound' | 'crtGlow') => {
    dispatch({ type: 'TOGGLE_EFFECT', effect });
  }, []);

  const setWindowPosition = useCallback((x: number, y: number) => {
    dispatch({ type: 'SET_WINDOW_POSITION', x, y });
  }, []);

  const setWindowSize = useCallback((width: number, height: number) => {
    dispatch({ type: 'SET_WINDOW_SIZE', width, height });
  }, []);

  const toggleMaximize = useCallback(() => {
    dispatch({ type: 'TOGGLE_MAXIMIZE' });
  }, []);

  const toggleMinimize = useCallback(() => {
    dispatch({ type: 'TOGGLE_MINIMIZE' });
  }, []);

  const setVisible = useCallback((isVisible: boolean) => {
    dispatch({ type: 'SET_VISIBLE', isVisible });
  }, []);

  const getHistoryCommand = useCallback((): string | null => {
    const { commandHistory, commandHistoryIndex } = state.terminal;
    if (commandHistoryIndex === -1 || commandHistory.length === 0) {
      return null;
    }
    return commandHistory[commandHistoryIndex] || null;
  }, [state.terminal]);

  const value: TerminalContextValue = {
    state,
    executeCommand: execCommand,
    setSystem,
    clear,
    navigateHistory,
    toggleEffect,
    setWindowPosition,
    setWindowSize,
    toggleMaximize,
    toggleMinimize,
    setVisible,
    getHistoryCommand,
    confirmAction,
  };

  return (
    <TerminalContext.Provider value={value}>
      {children}
    </TerminalContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function useTerminal(): TerminalContextValue {
  const context = useContext(TerminalContext);
  if (!context) {
    throw new Error('useTerminal must be used within a TerminalProvider');
  }
  return context;
}

export default TerminalContext;
