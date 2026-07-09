// Created at: 2026-07-08 22:04 EDT
// Created by: Codex
// Last Modified at: 2026-07-08 22:04 EDT
// Last Modified by: Codex

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { api } from '@ui/assets/api';
import './LogoutButton.css';

const TOKEN_KEY = 'catachess_token';
const USER_ID_KEY = 'catachess_user_id';

interface LogoutButtonProps {
  onLogout?: () => void;
}

const LogoutButton: React.FC<LogoutButtonProps> = ({ onLogout }) => {
  const [showDialog, setShowDialog] = useState(false);
  const dialogRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleLogoutClick = () => {
    setShowDialog(true);
  };

  const handleCancel = () => {
    setShowDialog(false);
  };

  const handleConfirm = async () => {
    try {
      // Call logout API
      await api.post('/auth/logout', {});
    } catch (error) {
      console.error('Logout API call failed:', error);
      // Continue with logout even if API call fails
    } finally {
      // Clear tokens
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_ID_KEY);
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_ID_KEY);

      // Call optional callback
      if (onLogout) {
        onLogout();
      }

      // Redirect to login
      window.location.assign('/login');
    }
  };

  // Handle click outside dialog
  useEffect(() => {
    if (!showDialog) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        dialogRef.current &&
        !dialogRef.current.contains(event.target as Node)
      ) {
        setShowDialog(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setShowDialog(false);
      }
    };

    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showDialog]);

  return (
    <div className="logout-button-wrapper">
      <button
        ref={buttonRef}
        className="logout-button"
        onClick={handleLogoutClick}
      >
        Log out
      </button>
      {showDialog && createPortal(
        <div className="logout-dialog-backdrop" role="presentation">
          <div
            ref={dialogRef}
            className="logout-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="logout-dialog-title"
          >
            <div className="logout-dialog__header">
              <span className="logout-dialog__eyebrow">Account</span>
              <h2 id="logout-dialog-title" className="logout-dialog__title">Log out?</h2>
            </div>
            <p className="logout-dialog-text">
              You will need to sign in again before opening your private workspace.
            </p>
            <div className="logout-dialog-buttons">
              <button className="logout-dialog-btn logout-btn-no" onClick={handleCancel}>
                Cancel
              </button>
              <button className="logout-dialog-btn logout-btn-yes" onClick={handleConfirm}>
                Log out
              </button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
};

export default LogoutButton;
