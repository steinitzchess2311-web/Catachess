/**
 * Created at: 2026-07-09 01:05 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-09 01:05 EDT
 * Last Modified by: Codex
 *
 * ToggleButton component - sidebar collapse/expand control.
 */

import React from "react";
import { ChevronLeftIcon, ChevronRightIcon } from "@radix-ui/react-icons";
import { ToggleButtonProps } from "./types";

const ToggleButton: React.FC<ToggleButtonProps> = ({
  isOpen,
  onOpenChange,
}) => {
  return (
    <button
      type="button"
      aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
      onClick={() => onOpenChange(!isOpen)}
      className="blog-sidebar-toggle"
    >
      {isOpen ? <ChevronLeftIcon width={20} height={20} /> : <ChevronRightIcon width={20} height={20} />}
    </button>
  );
};

export default ToggleButton;
