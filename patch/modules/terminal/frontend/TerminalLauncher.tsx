import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { TerminalProvider } from './terminalContext';
import { TerminalWindow } from './TerminalWindow';
import type { SystemType } from './types';

interface TerminalLauncherProps {
  /** Initial system style */
  initialSystem?: SystemType;
  /** Custom class for the trigger button */
  className?: string;
  /** Hotkey to toggle terminal (default: F12) */
  hotkey?: string;
}

/**
 * Fixed-position terminal launcher button
 * Renders a small icon in the bottom-right corner that opens the terminal
 * Also responds to F12 (or custom hotkey) to toggle
 */
export function TerminalLauncher({
  initialSystem = 'dos',
  className,
  hotkey = 'F12',
}: TerminalLauncherProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const toggleTerminal = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  // Keyboard shortcut handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Check for hotkey (default F12)
      if (e.key === hotkey || e.code === hotkey) {
        e.preventDefault();
        toggleTerminal();
      }
      // Also support Ctrl + ` as alternative
      if (e.key === '`' && e.ctrlKey) {
        e.preventDefault();
        toggleTerminal();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [hotkey, toggleTerminal]);

  const launcher = (
    <>
      {/* Fixed trigger button */}
      <button
        type="button"
        className={`terminal-launcher ${className || ''} ${isHovered ? 'is-hovered' : ''}`}
        onClick={toggleTerminal}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        title="Open Terminal (F12)"
        aria-label="Open Terminal"
        style={{
          position: 'fixed',
          right: 20,
          bottom: 20,
          width: 48,
          height: 48,
          borderRadius: 8,
          border: 'none',
          cursor: 'pointer',
          background: '#1a1a1a',
          color: '#00ff00',
          zIndex: 99999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span className="terminal-launcher-icon">
          {'>_'}
        </span>
      </button>

      {/* Terminal window */}
      {isOpen && (
        <TerminalProvider initialSystem={initialSystem}>
          <TerminalWindow onClose={() => setIsOpen(false)} />
        </TerminalProvider>
      )}
    </>
  );

  if (typeof document !== 'undefined' && document.body) {
    return createPortal(launcher, document.body);
  }
  return launcher;
}

export default TerminalLauncher;
