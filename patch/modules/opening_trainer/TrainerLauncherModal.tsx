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
        <div className="trainer-launcher-head">
          <h3>Choose Training Deck</h3>
          <p>Pick a training loop for this study. You can switch later any time.</p>
        </div>

        <div className="trainer-launcher-grid">
          <button type="button" className="trainer-launcher-card" onClick={onSelectPositionTrainer}>
            <span className="trainer-launcher-badge">Classic</span>
            <strong>Position Trainer</strong>
            <small>Freeze current board and drill calculation in local variations.</small>
            <div className="trainer-launcher-points">
              <span>Single position focus</span>
              <span>Fast tactical reps</span>
            </div>
          </button>

          <button type="button" className="trainer-launcher-card" onClick={onSelectOpeningTrainer}>
            <span className="trainer-launcher-badge is-blue">New</span>
            <strong>Opening Trainer</strong>
            <small>Split repertoire into units, run quiz loops, and track 3-streak mastery.</small>
            <div className="trainer-launcher-points">
              <span>Unit-based progression</span>
              <span>Long-term mastery stats</span>
            </div>
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
