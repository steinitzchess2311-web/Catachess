/**
 * TrainEntryModal.tsx - Intro modal shown before entering train mode.
 */

import React from 'react';
import './train.css';

interface TrainEntryModalProps {
  onCancel: () => void;
  onConfirm: () => void;
}

export function TrainEntryModal({ onCancel, onConfirm }: TrainEntryModalProps) {
  return (
    <div className="train-modal-overlay">
      <div className="train-modal">
        <h3 className="train-modal-title">Train Mode</h3>
        <p className="train-modal-body">
          In train mode you practice visualization and calculation — just like in a tournament.
          The board is frozen at the current position. Build your analysis in the draft editor,
          then submit to merge it into the study. Engine lines become available after you submit.
        </p>
        <p className="train-modal-tip">
          This is the most effective method for imitating a true tournament situation.
        </p>
        <div className="train-modal-actions">
          <button type="button" className="train-btn train-btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button type="button" className="train-btn train-btn-primary" onClick={onConfirm}>
            Enter Train Mode
          </button>
        </div>
      </div>
    </div>
  );
}

export default TrainEntryModal;
