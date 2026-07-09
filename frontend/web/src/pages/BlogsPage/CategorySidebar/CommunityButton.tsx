/**
 * Created at: 2026-07-09 01:34 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:34 EDT
 * Last Modified by: Codex
 *
 * CommunityButton component - user community navigation.
 */

import React from "react";
import { ReaderIcon } from "@radix-ui/react-icons";
import { CommunityButtonProps } from "./types";

const CommunityButton: React.FC<CommunityButtonProps> = ({
  activeCategory,
  onUserBlogsClick,
}) => {
  return (
    <button
      onClick={onUserBlogsClick}
      className={`blog-sidebar-item${activeCategory === "user" ? " is-active" : ""}`}
    >
      <ReaderIcon width={18} height={18} />
      <span className="blog-sidebar-item__label">Community</span>
    </button>
  );
};

export default CommunityButton;
