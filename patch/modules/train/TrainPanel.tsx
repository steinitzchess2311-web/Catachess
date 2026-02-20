/**
 * TrainPanel.tsx - Right-panel container for train mode.
 *
 * - Header: "Train Mode" label + Exit button
 * - Body: DraftTree (scrollable)
 * - Footer: Submit button (disabled if !isSubmittable)
 */

import React, { useRef } from 'react';
import { useStudy } from '../../studyContext';
import { useDraftTree } from './useDraftTree';
import { mergeTrainTree } from './mergeTrainTree';
import { DraftTree } from './DraftTree';
import './train.css';

export function TrainPanel() {
  const { state, exitTrainMode, submitTrain, saveTree } = useStudy();

  // Freeze the anchor position at mount time.
  // Arrow-key navigation is still allowed during train mode, but the draft tree
  // and the merge anchor stay fixed to where train mode was entered.
  const anchorNodeIdRef = useRef(state.cursorNodeId);
  const anchorFenRef = useRef(state.currentFen);

  const draft = useDraftTree(anchorFenRef.current, anchorNodeIdRef.current);

  const handleSubmit = () => {
    if (!draft.isSubmittable) return;
    const merged = mergeTrainTree(
      state.tree,
      draft.nodes,
      draft.rootId,
      anchorNodeIdRef.current
    );
    submitTrain(merged);
    // saveTree() will be triggered by auto-save (isDirty: true after SUBMIT_TRAIN)
    // but we also fire it immediately for a faster save
    saveTree();
  };

  return (
    <div className="train-panel">
      <div className="train-panel-header">
        <span className="train-panel-title">Train Mode</span>
        <button
          type="button"
          className="train-btn train-btn-exit"
          onClick={exitTrainMode}
          title="Exit train mode (draft will be discarded)"
        >
          Exit
        </button>
      </div>

      <div className="train-panel-body">
        <DraftTree draft={draft} />
      </div>

      <div className="train-panel-footer">
        <button
          type="button"
          className={`train-btn train-btn-submit${draft.isSubmittable ? '' : ' is-disabled'}`}
          onClick={handleSubmit}
          disabled={!draft.isSubmittable}
          title={draft.isSubmittable ? 'Submit your analysis' : 'Add at least one move to submit'}
        >
          Submit Analysis
        </button>
        {!draft.isSubmittable && (
          <span className="train-submit-hint">Add moves to enable submit</span>
        )}
      </div>
    </div>
  );
}

export default TrainPanel;
