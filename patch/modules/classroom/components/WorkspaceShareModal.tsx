/**
 * WorkspaceShareModal
 * ───────────────────
 * Student picks a workspace node (study or folder) to share with the teacher.
 *
 * Now delegates the browsing UI to <WorkspacePicker> and only handles
 * the share-to-teacher action + error / success states.
 *
 * Uses inline styles + cl-* CSS variables (classroom design system).
 */

import React, { useCallback, useState } from 'react';
import { shareToTeacher } from '../api';
import { WorkspacePicker, type PickerNode } from '../../../components/WorkspacePicker';

interface Props {
  classroomId: string;
  onClose: () => void;
  /** Called after a successful share with the shared node's title. */
  onShared: (nodeTitle: string) => void;
}

export const WorkspaceShareModal: React.FC<Props> = ({ classroomId, onClose, onShared }) => {
  const [sharing, setSharing] = useState<string | null>(null);

  const handleSelect = useCallback(async (node: PickerNode) => {
    if (sharing) return;
    setSharing(node.id);
    try {
      await shareToTeacher(classroomId, node.id);
      onShared(node.title);
    } catch (e) {
      // WorkspacePicker shows its own error state; re-throw not needed
      // but we reset sharing so user can retry
      setSharing(null);
    }
  }, [classroomId, sharing, onShared]);

  return (
    <WorkspacePicker
      selectable={['folder', 'study']}
      onSelect={handleSelect}
      onClose={onClose}
      title="Share to Teacher"
      selectLabel="Share"
      busyNodeId={sharing}
    />
  );
};
