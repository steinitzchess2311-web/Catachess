/**
 * Created at: 2026-07-09 01:34 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:34 EDT
 * Last Modified by: Codex
 *
 * PinnedButton component - pinned articles navigation.
 */

import React from "react";
import { DrawingPinFilledIcon } from "@radix-ui/react-icons";
import { PinnedButtonProps } from "./types";

const PinnedButton: React.FC<PinnedButtonProps> = ({
  activeCategory,
  onCategoryChange,
  onViewModeChange,
}) => {
  return (
    <button
      onClick={() => {
        onCategoryChange('pinned');
        onViewModeChange('articles');
      }}
      className={`blog-sidebar-item${activeCategory === "pinned" ? " is-active" : ""}`}
    >
      <DrawingPinFilledIcon width={18} height={18} />
      <span>Pinned Articles</span>
    </button>
  );
};

export default PinnedButton;
