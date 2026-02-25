/**
 * ToggleButton component - Sidebar collapse/expand control
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
      aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
      onClick={() => onOpenChange(!isOpen)}
      style={{
        position: "absolute",
        top: "10px",
        right: "10px",
        width: "34px",
        height: "34px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: "none",
        background: "rgba(37, 99, 235, 0.12)",
        borderRadius: "8px",
        cursor: "pointer",
        color: "#2563eb",
        transition: "all 0.2s ease",
        zIndex: 10,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = "rgba(37, 99, 235, 0.2)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(37, 99, 235, 0.1)";
      }}
    >
      {isOpen ? <ChevronLeftIcon width={20} height={20} /> : <ChevronRightIcon width={20} height={20} />}
    </button>
  );
};

export default ToggleButton;
