/**
 * ExitConfirmDialog - Popover shown when closing the editor with unsaved changes
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
    <div
      style={{
        position: 'absolute',
        top: '50px',
        right: '0',
        background: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)',
        padding: '20px',
        zIndex: 10001,
        minWidth: '280px',
        border: '1px solid #e2e8f0',
      }}
    >
      <div style={{ marginBottom: '16px', fontSize: '0.95rem', color: '#0f172a', fontWeight: 600 }}>
        Do you want to save your changes?
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button
          onClick={onSaveAndExit}
          disabled={saving}
          style={{
            width: '100%',
            padding: '10px 16px',
            fontSize: '0.9rem',
            fontWeight: 500,
            color: 'white',
            backgroundColor: '#2563eb',
            border: 'none',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.5 : 1,
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => { if (!saving) e.currentTarget.style.backgroundColor = '#6f5a42'; }}
          onMouseLeave={(e) => { if (!saving) e.currentTarget.style.backgroundColor = '#2563eb'; }}
        >
          {saving ? 'Saving...' : 'Save and Exit'}
        </button>

        <button
          onClick={onDiscard}
          disabled={saving}
          style={{
            width: '100%',
            padding: '10px 16px',
            fontSize: '0.9rem',
            fontWeight: 500,
            color: '#dc3545',
            backgroundColor: 'transparent',
            border: '1px solid #dc3545',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.5 : 1,
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            if (!saving) {
              e.currentTarget.style.backgroundColor = '#dc3545';
              e.currentTarget.style.color = 'white';
            }
          }}
          onMouseLeave={(e) => {
            if (!saving) {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#dc3545';
            }
          }}
        >
          Discard
        </button>

        <button
          onClick={onCancel}
          disabled={saving}
          style={{
            width: '100%',
            padding: '10px 16px',
            fontSize: '0.9rem',
            fontWeight: 500,
            color: '#475569',
            backgroundColor: 'transparent',
            border: '1px solid #e2e8f0',
            borderRadius: '6px',
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.5 : 1,
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => { if (!saving) e.currentTarget.style.backgroundColor = '#f0f0f0'; }}
          onMouseLeave={(e) => { if (!saving) e.currentTarget.style.backgroundColor = 'transparent'; }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

export default ExitConfirmDialog;
