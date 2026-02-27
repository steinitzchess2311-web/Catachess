import React from 'react';
import './trainer_launcher.css';

interface TrainerLauncherModalProps {
  onClose: () => void;
  onSelectPositionTrainer: () => void;
  onSelectOpeningTrainer: () => void;
}

export function TrainerLauncherModal({
  onClose,
  onSelectPositionTrainer,
  onSelectOpeningTrainer,
}: TrainerLauncherModalProps) {
  return (
    <div className="trainer-launcher-overlay" role="dialog" aria-modal="true">
      <div className="trainer-launcher-modal">
        <h3>Choose Trainer</h3>
        <p>Pick your training mode for this study.</p>
        <div className="trainer-launcher-grid">
          <button type="button" className="trainer-launcher-card" onClick={onSelectPositionTrainer}>
            <span className="trainer-launcher-badge">Classic</span>
            <strong>Position Trainer</strong>
            <small>Freeze current board and train calculation with draft variations.</small>
          </button>
          <button type="button" className="trainer-launcher-card" onClick={onSelectOpeningTrainer}>
            <span className="trainer-launcher-badge is-blue">New</span>
            <strong>Opening Trainer</strong>
            <small>Split repertoire into units, run quiz loops, and track 3-streak mastery.</small>
          </button>
        </div>
        <div className="trainer-launcher-actions">
          <button type="button" className="trainer-launcher-cancel" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default TrainerLauncherModal;

