/**
 * CommunityButton component - User community navigation
 */

import React from "react";
import { CommunityButtonProps } from "./types";

const CommunityButton: React.FC<CommunityButtonProps> = ({
  activeCategory,
  onUserBlogsClick,
}) => {
  return (
    <button
      onClick={onUserBlogsClick}
      style={{
        background: activeCategory === "user" ? "rgba(37, 99, 235, 0.1)" : "transparent",
        border: "none",
        borderLeft: activeCategory === "user" ? "4px solid #2563eb" : "4px solid transparent",
        padding: "14px 25px",
        textAlign: "left",
        cursor: "pointer",
        fontSize: "0.95rem",
        fontWeight: activeCategory === "user" ? 600 : 500,
        color: activeCategory === "user" ? "#0f172a" : "#475569",
        transition: "all 0.2s ease",
        display: "flex",
        alignItems: "center",
        gap: "10px",
        width: "100%",
      }}
      onMouseEnter={(e) => {
        if (activeCategory !== "user") {
          e.currentTarget.style.background = "rgba(37, 99, 235, 0.05)";
        }
      }}
      onMouseLeave={(e) => {
        if (activeCategory !== "user") {
          e.currentTarget.style.background = "transparent";
        }
      }}
    >
      <span style={{ fontSize: "1.2rem" }}>✍️</span>
      <span style={{ flex: 1 }}>Community</span>
    </button>
  );
};

export default CommunityButton;
