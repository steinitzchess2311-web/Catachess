/**
 * OfficialSection component - Chessortag Official always expanded section
 */

import React from "react";
import pureLogo from "../../../assets/chessortag_pure_logo.png";
import { OfficialSectionProps } from "./types";

const OfficialSection: React.FC<OfficialSectionProps> = ({
  activeCategory,
  isOfficialOpen,
  setIsOfficialOpen,
  onCategoryClick,
}) => {
  const officialSubItems = [
    { id: "about", label: "Our Stories" },
    { id: "function", label: "Functions Intro" },
    { id: "devlog", label: "Developer Logs" },
  ];

  // Check if any official category is active (including allblogs)
  const isOfficialActive = activeCategory === 'about' ||
                          activeCategory === 'function' ||
                          activeCategory === undefined;

  return (
    <div>
      {/* Chessortag Official Header Button */}
      <button
        onClick={() => onCategoryClick('allblogs')}
        style={{
          background: (activeCategory === undefined || activeCategory === 'allblogs') ? "rgba(139, 115, 85, 0.1)" : "transparent",
          border: "none",
          borderLeft: (activeCategory === undefined || activeCategory === 'allblogs') ? "4px solid #2563eb" : "4px solid transparent",
          padding: "14px 25px",
          textAlign: "left",
          cursor: "pointer",
          fontSize: "0.95rem",
          fontWeight: (activeCategory === undefined || activeCategory === 'allblogs') ? 600 : 500,
          color: (activeCategory === undefined || activeCategory === 'allblogs') ? "#0f172a" : "#475569",
          transition: "all 0.2s ease",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          width: "100%",
        }}
        onMouseEnter={(e) => {
          if (activeCategory !== undefined && activeCategory !== 'allblogs') {
            e.currentTarget.style.background = "rgba(139, 115, 85, 0.05)";
          }
        }}
        onMouseLeave={(e) => {
          if (activeCategory !== undefined && activeCategory !== 'allblogs') {
            e.currentTarget.style.background = "transparent";
          }
        }}
      >
        <img
          src={pureLogo}
          alt="Chessortag"
          style={{
            width: "24px",
            height: "24px",
            objectFit: "contain",
          }}
        />
        <span style={{ flex: 1 }}>Chessortag Official</span>
      </button>

      {/* Sub-items - Always visible */}
      <div
        style={{
          paddingLeft: "54px",
          paddingTop: "4px",
          paddingBottom: "4px",
        }}
      >
        {officialSubItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onCategoryClick(item.id)}
            style={{
              background: activeCategory === item.id ? "rgba(139, 115, 85, 0.08)" : "transparent",
              border: "none",
              padding: "10px 25px 10px 20px",
              textAlign: "left",
              cursor: "pointer",
              fontSize: "0.9rem",
              fontWeight: activeCategory === item.id ? 600 : 400,
              color: activeCategory === item.id ? "#2563eb" : "#64748b",
              transition: "all 0.15s ease",
              display: "block",
              width: "100%",
              borderRadius: "6px",
              marginBottom: "2px",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(139, 115, 85, 0.08)";
              e.currentTarget.style.color = "#2563eb";
            }}
            onMouseLeave={(e) => {
              if (activeCategory !== item.id) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "#64748b";
              }
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default OfficialSection;
