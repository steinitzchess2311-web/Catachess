/**
 * PinnedButton component - Pinned articles navigation
 */

import React from "react";
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
      style={{
        background: activeCategory === "pinned" ? "rgba(37, 99, 235, 0.1)" : "transparent",
        border: "none",
        borderLeft: activeCategory === "pinned" ? "4px solid #2563eb" : "4px solid transparent",
        padding: "14px 25px",
        textAlign: "left",
        cursor: "pointer",
        fontSize: "0.95rem",
        fontWeight: activeCategory === "pinned" ? 600 : 500,
        color: activeCategory === "pinned" ? "#0f172a" : "#475569",
        transition: "all 0.2s ease",
        display: "flex",
        alignItems: "center",
        gap: "10px",
      }}
      onMouseEnter={(e) => {
        if (activeCategory !== "pinned") {
          e.currentTarget.style.background = "rgba(37, 99, 235, 0.05)";
        }
      }}
      onMouseLeave={(e) => {
        if (activeCategory !== "pinned") {
          e.currentTarget.style.background = "transparent";
        }
      }}
    >
      <span style={{ fontSize: "1.2rem" }}>📌</span>
      <span>Pinned Articles</span>
    </button>
  );
};

export default PinnedButton;
