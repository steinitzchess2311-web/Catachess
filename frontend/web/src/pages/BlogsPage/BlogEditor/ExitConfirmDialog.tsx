/**
 * Created at: 2026-07-09 01:31 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:31 EDT
 * Last Modified by: Codex
 *
 * ExitConfirmDialog - popover shown when closing the editor with unsaved changes.
 */

import React from 'react';

interface ExitConfirmDialogProps {
  saving: boolean;
  onSaveAndExit: () => void;
  onDiscard: () => void;
  onCancel: () => void;
}

const ExitConfirmDialog: React.FC<ExitConfirmDialogProps> = ({
  saving,
  onSaveAndExit,
  onDiscard,
  onCancel,
}) => {
  return (
    <div className="blog-editor-exit-popover">
      <div className="blog-editor-exit-title">
        Do you want to save your changes?
      </div>
      <div className="blog-editor-exit-actions">
        <button
          onClick={onSaveAndExit}
          disabled={saving}
          className="blog-editor-exit-button is-primary"
        >
          {saving ? 'Saving...' : 'Save and Exit'}
        </button>

        <button
          onClick={onDiscard}
          disabled={saving}
          className="blog-editor-exit-button is-danger"
        >
          Discard
        </button>

        <button
          onClick={onCancel}
          disabled={saving}
          className="blog-editor-exit-button"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default ExitConfirmDialog;
