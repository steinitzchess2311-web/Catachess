/**
 * CollapsedView component - Minimal icon view when sidebar is collapsed
 */

import React from "react";
import pureLogo from "../../../assets/chessortag_pure_logo.png";
import { CollapsedViewProps } from "./types";

const CollapsedView: React.FC<CollapsedViewProps> = ({
  activeCategory,
  isOfficialOpen,
  setIsOfficialOpen,
  onCategoryChange,
  onViewModeChange,
  onUserBlogsClick,
  userRole,
  setEditorOpen,
}) => {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "20px",
        paddingTop: "52px",
      }}
    >
      {/* Pinned Icon */}
      <button
        onClick={() => {
          onCategoryChange('pinned');
          onViewModeChange('articles');
        }}
        style={{
          width: "36px",
          height: "36px",
          border: "none",
          background: activeCategory === "pinned" ? "rgba(37, 99, 235, 0.2)" : "transparent",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "1.2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(37, 99, 235, 0.15)";
        }}
        onMouseLeave={(e) => {
          if (activeCategory !== "pinned") {
            e.currentTarget.style.background = "transparent";
          }
        }}
        title="Pinned Articles"
      >
        📌
      </button>

      {/* Community Icon */}
      <button
        onClick={onUserBlogsClick}
        style={{
          width: "36px",
          height: "36px",
          border: "none",
          background: activeCategory === "user" ? "rgba(37, 99, 235, 0.2)" : "transparent",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "1.2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(37, 99, 235, 0.15)";
        }}
        onMouseLeave={(e) => {
          if (activeCategory !== "user") {
            e.currentTarget.style.background = "transparent";
          }
        }}
        title="Community"
      >
        ✍️
      </button>

      {/* Official Logo Icon - Navigate to all official blogs */}
      <button
        onClick={() => {
          onCategoryChange('allblogs');
          onViewModeChange('articles');
        }}
        style={{
          width: "36px",
          height: "36px",
          border: "none",
          background: (activeCategory === undefined || activeCategory === 'allblogs') ? "rgba(37, 99, 235, 0.2)" : "transparent",
          borderRadius: "8px",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          transition: "all 0.2s ease",
          padding: "6px",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = "rgba(37, 99, 235, 0.15)";
        }}
        onMouseLeave={(e) => {
          if (activeCategory !== undefined && activeCategory !== 'allblogs') {
            e.currentTarget.style.background = "transparent";
          }
        }}
        title="Chessortag Official"
      >
        <img
          src={pureLogo}
          alt="Chessortag"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
          }}
        />
      </button>

      {/* Create Button - Only for Editor/Admin */}
      {(userRole === 'editor' || userRole === 'admin') && (
        <button
          onClick={() => setEditorOpen(true)}
          style={{
            width: "36px",
            height: "36px",
            border: "2px solid #2563eb",
            background: "transparent",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "1.2rem",
            color: "#2563eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s ease",
            marginTop: "20px",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "rgba(37, 99, 235, 0.08)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = "transparent";
          }}
          title="Create Article"
        >
          +
        </button>
      )}
    </div>
  );
};

export default CollapsedView;
