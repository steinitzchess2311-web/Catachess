/**
 * DeleteConfirmDialog - Modern minimalist confirmation dialog
 * Appears near the delete button with clean design
 */

import React from "react";
import { Cross2Icon, CheckIcon } from "@radix-ui/react-icons";

interface DeleteConfirmDialogProps {
  show: boolean;
  dialogRef: React.RefObject<HTMLDivElement>;
  onConfirm: () => void;
  onCancel: () => void;
}

const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
  show,
  dialogRef,
  onConfirm,
  onCancel,
}) => {
  if (!show) return null;

  return (
    <>
      <div
        ref={dialogRef}
        style={{
          position: 'absolute',
          top: '50px',
          right: '12px',
          width: '220px',
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
          padding: '20px',
          zIndex: 1001,
          animation: 'dialogFadeIn 0.2s ease-out',
        }}
      >
        <p
          style={{
            margin: '0 0 16px 0',
            fontSize: '0.95rem',
            color: '#0f172a',
            textAlign: 'center',
            lineHeight: '1.5',
            fontWeight: 500,
          }}
        >
          Delete this article?
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onCancel();
            }}
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              border: 'none',
              backgroundColor: '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              color: '#666',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#4a9eff';
              e.currentTarget.style.color = 'white';
              e.currentTarget.style.transform = 'scale(1.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#f0f0f0';
              e.currentTarget.style.color = '#666';
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            <Cross2Icon width={20} height={20} />
          </button>
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onConfirm();
            }}
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              border: 'none',
              backgroundColor: '#f0f0f0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              color: '#666',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#dc3545';
              e.currentTarget.style.color = 'white';
              e.currentTarget.style.transform = 'scale(1.1)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = '#f0f0f0';
              e.currentTarget.style.color = '#666';
              e.currentTarget.style.transform = 'scale(1)';
            }}
          >
            <CheckIcon width={20} height={20} />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes dialogFadeIn {
          from {
            opacity: 0;
            transform: translateY(-8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </>
  );
};

export default DeleteConfirmDialog;
