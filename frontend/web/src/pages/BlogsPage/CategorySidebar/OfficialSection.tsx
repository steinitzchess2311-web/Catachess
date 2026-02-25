/**
 * OfficialSection component - Chessortag Official always expanded section
 */

import React from "react";
import pureLogo from "../../../assets/chessortag_pure_logo.png";
import { ChevronDownIcon } from "@radix-ui/react-icons";
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

  const isOfficialRootActive = activeCategory === undefined || activeCategory === 'allblogs' || activeCategory === 'official';

  return (
    <div>
      {/* Chessortag Official Header Button */}
      <button
        onClick={() => {
          onCategoryClick('allblogs');
          setIsOfficialOpen((prev) => !prev);
        }}
        style={{
          background: isOfficialRootActive ? "rgba(37, 99, 235, 0.1)" : "transparent",
          border: "none",
          borderLeft: isOfficialRootActive ? "4px solid #2563eb" : "4px solid transparent",
          padding: "14px 25px",
          textAlign: "left",
          cursor: "pointer",
          fontSize: "0.95rem",
          fontWeight: isOfficialRootActive ? 600 : 500,
          color: isOfficialRootActive ? "#0f172a" : "#475569",
          transition: "all 0.2s ease",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          width: "100%",
        }}
        onMouseEnter={(e) => {
          if (!isOfficialRootActive) {
            e.currentTarget.style.background = "rgba(37, 99, 235, 0.05)";
          }
        }}
        onMouseLeave={(e) => {
          if (!isOfficialRootActive) {
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
        <ChevronDownIcon
          width={18}
          height={18}
          style={{
            transform: isOfficialOpen ? "rotate(0deg)" : "rotate(-90deg)",
            transition: "transform 0.18s ease",
            opacity: 0.75,
          }}
        />
      </button>

      {/* Sub-items */}
      <div
        style={{
          paddingLeft: "54px",
          paddingTop: isOfficialOpen ? "4px" : "0px",
          paddingBottom: isOfficialOpen ? "4px" : "0px",
          maxHeight: isOfficialOpen ? "220px" : "0px",
          opacity: isOfficialOpen ? 1 : 0,
          overflow: "hidden",
          transition: "max-height 0.22s ease, opacity 0.22s ease, padding 0.22s ease",
        }}
      >
        {officialSubItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onCategoryClick(item.id)}
            style={{
              background: activeCategory === item.id ? "rgba(37, 99, 235, 0.08)" : "transparent",
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
              e.currentTarget.style.background = "rgba(37, 99, 235, 0.08)";
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
