/**
 * Created at: 2026-07-09 01:34 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:34 EDT
 * Last Modified by: Codex
 *
 * CollapsedView component - minimal icon view when sidebar is collapsed.
 */

import React from "react";
import { DrawingPinFilledIcon, PlusIcon, ReaderIcon } from "@radix-ui/react-icons";
import pureLogo from "../../../assets/chessortag_pure_logo.png";
import { CollapsedViewProps } from "./types";

const CollapsedView: React.FC<CollapsedViewProps> = ({
  activeCategory,
  onCategoryChange,
  onViewModeChange,
  onUserBlogsClick,
  userRole,
  setEditorOpen,
}) => {
  return (
    <div className="blog-sidebar-rail">
      {/* Pinned Icon */}
      <button
        onClick={() => {
          onCategoryChange('pinned');
          onViewModeChange('articles');
        }}
        className={`blog-sidebar-rail__button${activeCategory === "pinned" ? " is-active" : ""}`}
        title="Pinned Articles"
      >
        <DrawingPinFilledIcon width={18} height={18} />
      </button>

      {/* Community Icon */}
      <button
        onClick={onUserBlogsClick}
        className={`blog-sidebar-rail__button${activeCategory === "user" ? " is-active" : ""}`}
        title="Community"
      >
        <ReaderIcon width={18} height={18} />
      </button>

      {/* Official Logo Icon - Navigate to all official blogs */}
      <button
        onClick={() => {
          onCategoryChange('allblogs');
          onViewModeChange('articles');
        }}
        className={`blog-sidebar-rail__button${(activeCategory === undefined || activeCategory === 'allblogs') ? " is-active" : ""}`}
        title="Chessortag Official"
      >
        <img
          src={pureLogo}
          alt="Chessortag"
          className="blog-sidebar-rail__logo"
        />
      </button>

      {/* Create Button - Only for Editor/Admin */}
      {(userRole === 'editor' || userRole === 'admin') && (
        <button
          onClick={() => setEditorOpen(true)}
          className="blog-sidebar-rail__button blog-sidebar-rail__button--create"
          title="Create Article"
        >
          <PlusIcon width={18} height={18} />
        </button>
      )}
    </div>
  );
};

export default CollapsedView;
