/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * UserActionsSection component - editor/admin blog actions.
 */

import React from "react";
import { FilePlusIcon, ReaderIcon, ArchiveIcon } from "@radix-ui/react-icons";
import { UserActionsSectionProps } from "./types";

const UserActionsSection: React.FC<UserActionsSectionProps> = ({
  userRole,
  viewMode,
  onViewModeChange,
  setEditorOpen,
}) => {
  if (userRole !== 'editor' && userRole !== 'admin') {
    return null;
  }

  return (
    <div className="blog-sidebar-actions">
      <button
        type="button"
        onClick={() => setEditorOpen(true)}
        className="blog-sidebar-action-primary"
      >
        <FilePlusIcon width={16} height={16} />
        <span>Create article</span>
      </button>

      <button
        type="button"
        onClick={() => onViewModeChange('drafts')}
        className={`blog-sidebar-action${viewMode === 'drafts' ? ' is-active' : ''}`}
      >
        <ArchiveIcon width={15} height={15} />
        <span>Draft box</span>
      </button>

      <button
        type="button"
        onClick={() => onViewModeChange('my-published')}
        className={`blog-sidebar-action${viewMode === 'my-published' ? ' is-active' : ''}`}
      >
        <ReaderIcon width={15} height={15} />
        <span>My published</span>
      </button>
    </div>
  );
};

export default UserActionsSection;
