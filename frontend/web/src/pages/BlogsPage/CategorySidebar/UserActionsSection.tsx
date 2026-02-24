/**
 * UserActionsSection component - Editor/Admin actions (Create, Drafts, My Published)
 */

import React from "react";
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
    <div
      style={{
        marginTop: "20px",
        paddingTop: "20px",
        borderTop: "1px solid rgba(139, 115, 85, 0.15)",
        paddingLeft: "25px",
        paddingRight: "25px",
      }}
    >
      {/* Create Button */}
      <button
        onClick={() => setEditorOpen(true)}
        style={{
          width: "100%",
          padding: "12px 16px",
          fontSize: "0.95rem",
          fontWeight: 500,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif",
          color: "#4a9eff",
          backgroundColor: "transparent",
          border: "2px solid #4a9eff",
          borderRadius: "8px",
          cursor: "pointer",
          transition: "all 0.2s ease",
          marginBottom: "12px",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = "rgba(74, 158, 255, 0.08)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = "transparent";
        }}
        onMouseDown={(e) => {
          e.currentTarget.style.transform = "scale(0.97)";
        }}
        onMouseUp={(e) => {
          e.currentTarget.style.transform = "scale(1)";
        }}
      >
        + Create Article
      </button>

      {/* Draft Box Button */}
      <button
        onClick={() => onViewModeChange('drafts')}
        style={{
          width: "100%",
          padding: "10px 16px",
          fontSize: "0.9rem",
          fontWeight: 500,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif",
          color: viewMode === 'drafts' ? "#2563eb" : "#475569",
          backgroundColor: viewMode === 'drafts' ? "rgba(139, 115, 85, 0.08)" : "transparent",
          border: "1px solid rgba(139, 115, 85, 0.3)",
          borderRadius: "6px",
          cursor: "pointer",
          transition: "all 0.2s ease",
          marginBottom: "8px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
        onMouseEnter={(e) => {
          if (viewMode !== 'drafts') {
            e.currentTarget.style.backgroundColor = "rgba(139, 115, 85, 0.05)";
          }
        }}
        onMouseLeave={(e) => {
          if (viewMode !== 'drafts') {
            e.currentTarget.style.backgroundColor = "transparent";
          }
        }}
      >
        <span>📝</span>
        <span>Draft Box</span>
      </button>

      {/* My Published Blogs Button */}
      <button
        onClick={() => onViewModeChange('my-published')}
        style={{
          width: "100%",
          padding: "10px 16px",
          fontSize: "0.9rem",
          fontWeight: 500,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, sans-serif",
          color: viewMode === 'my-published' ? "#2563eb" : "#475569",
          backgroundColor: viewMode === 'my-published' ? "rgba(139, 115, 85, 0.08)" : "transparent",
          border: "1px solid rgba(139, 115, 85, 0.3)",
          borderRadius: "6px",
          cursor: "pointer",
          transition: "all 0.2s ease",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
        onMouseEnter={(e) => {
          if (viewMode !== 'my-published') {
            e.currentTarget.style.backgroundColor = "rgba(139, 115, 85, 0.05)";
          }
        }}
        onMouseLeave={(e) => {
          if (viewMode !== 'my-published') {
            e.currentTarget.style.backgroundColor = "transparent";
          }
        }}
      >
        <span>📚</span>
        <span>My Published Blogs</span>
      </button>
    </div>
  );
};

export default UserActionsSection;
